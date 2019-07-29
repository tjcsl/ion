import logging
import os
import threading
import shutil
import traceback
import datetime
import csv

from tempfile import gettempdir
from io import StringIO

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect
from django.core.management import call_command
from django.contrib import messages
from django.contrib.auth import get_user_model

from ....auth.decorators import eighth_admin_required, reauthentication_required

from ....users.models import Address, Course, Section

from ....notifications.tasks import email_send_task

logger = logging.getLogger(__name__)


@eighth_admin_required
@reauthentication_required
def index_view(request):
    context = {"admin_page_title": "Maintenance Tools"}
    return render(request, "eighth/admin/maintenance.html", context)


def get_import_directory():
    return os.path.join(gettempdir(), "ion_sis_import")


class ImportThread(threading.Thread):
    def __init__(self, email, folder):
        threading.Thread.__init__(self)
        self.email = email
        self.folder = folder
        logger.debug(self.folder)
        logger.debug(self.email)

    def handle_user(self, u, row, index_dict, content):
        # pylint: disable=protected-access
        u.first_name = row[index_dict["First Name"]].strip()
        u.last_name = row[index_dict["Last Name"]].strip()
        u.middle_name = row[index_dict["Middle Name"]].strip()
        u.nickname = row[index_dict["Nick Name"]].strip() if row[11].strip() != "" else None
        u.gender = row[index_dict["Gender"]].strip().upper() == "M"
        u.graduation_year = settings.SENIOR_GRADUATION_YEAR - int(row[index_dict["Grade"]].strip()) + 12
        counselor = get_user_model().objects.filter(user_type="counselor", last_name__iexact=row[index_dict["Counselor Last Name"]].strip())
        if counselor.exists():
            u.counselor = counselor.first()
        props = u.properties
        if props._address:
            props._address.delete()
        props._address = Address.objects.create(
            street=row[index_dict["Address"]].strip(),
            city=row[index_dict["City"]].strip(),
            state=row[index_dict["State"]].strip(),
            postal_code=row[index_dict["Zipcode"]].strip(),
        )
        birthday_values = row[index_dict["Birth Date"]].strip().split("/")
        props._birthday = "{}-{}-{}".format(birthday_values[2], birthday_values[0], birthday_values[1])
        course, _ = Course.objects.get_or_create(
            course_id=row[index_dict["Course ID"]].strip(), defaults={"name": row[index_dict["Course Title"]].strip()}
        )
        teacher_name = row[index_dict["Teacher"]].strip().lower().split(",")
        no_teacher = False
        if len(teacher_name) == 1:
            content.write("Unable to determine teacher for {} for {}".format(row[index_dict["Section ID"]].strip(), u.full_name))
            no_teacher = True
        if not no_teacher:
            fname = teacher_name[1].split()[0].strip()
            lname = teacher_name[0].strip()
            teacher = get_user_model().objects.filter(user_type="teacher", last_name__iexact=lname, first_name__iexact=fname)
        if not no_teacher and (not teacher.count() == 1):
            content.write(
                "Unable to determine teacher for {}; {} options: {}".format(
                    row[index_dict["Section ID"]].strip(), teacher.count(), ", ".join([t.full_name for t in teacher])
                )
            )
            no_teacher = True
        section, _ = Section.objects.get_or_create(
            section_id=row[index_dict["Section ID"]].strip(),
            defaults={
                "teacher": teacher.first() if not no_teacher else None,
                "period": int(row[index_dict["Per"]].strip()),
                "room": row[index_dict["Room"]].strip(),
                "sem": row[index_dict["Term Code"]].strip(),
                "course": course,
            },
        )
        section._students.add(props)
        props.save()
        u.save()

    def run(self):
        start_time = datetime.datetime.now()
        content = StringIO()
        failure = False

        try:
            content.write("=== Starting Import.\n\n")
            with open(os.path.join(self.folder, "data.csv"), "r") as f:
                reader = csv.reader(f)
                headers = next(reader)
                index_dict = {}
                for i, header in enumerate(headers):
                    index_dict[header.strip()] = i
                for row in reader:
                    try:
                        u = get_user_model().objects.get(student_id=row[index_dict["Student ID"]].strip())
                        self.handle_user(u, row, index_dict, content)
                        content.write("Updated information for {}\n".format(u.username))
                    except get_user_model().DoesNotExist:
                        if row[index_dict["Other Name"]].strip() == "":
                            content.write("Skipping {}, no username available and user does not exist in database\n".format(row))
                            continue
                        u = get_user_model().objects.create(
                            username=row[index_dict["Other Name"]].strip().lower(), student_id=row[index_dict["Student ID"]].strip()
                        )
                        self.handle_user(u, row, index_dict, content)
                        content.write("User {} did not exist in database - created and updated information\n".format(u.username))
            content.write("\n\n==== Successfully completed SIS Import\n\n")
        except Exception:
            failure = True
            content.write("\n=== An error occured during the import process!\n\n")
            content.write(traceback.format_exc())
            content.write("\n=== The import process has been aborted.")
        shutil.rmtree(self.folder)
        content.seek(0)
        logger.debug(content.read())
        content.seek(0)

        data = {"log": content.read(), "failure": failure, "help_email": settings.FEEDBACK_EMAIL, "date": start_time.strftime("%I:%M:%S %p %m/%d/%Y")}
        email_send_task.delay(
            "eighth/emails/import_notify.txt",
            "eighth/emails/import_notify.html",
            data,
            "SIS Import Results - {}".format("Failure" if failure else "Success"),
            [self.email],
        )


@eighth_admin_required
@reauthentication_required
def sis_import(request):
    import_dir = get_import_directory()
    context = {
        "admin_page_title": "SIS Import",
        "email": request.user.tj_email,
        "help_email": settings.FEEDBACK_EMAIL,
        "already_importing": os.path.isdir(import_dir),
        "completed": False,
    }
    if request.method == "POST":
        if context["already_importing"]:
            messages.error(request, "An upload is currently in progress!")
            return redirect(reverse("eighth_admin_maintenance_sis_import"))
        if not request.FILES:
            messages.error(request, "You need to upload a file!")
            return redirect(reverse("eighth_admin_maintenance_sis_import"))
        data = request.FILES["data"]
        os.makedirs(import_dir)
        with open(os.path.join(import_dir, "data.csv"), "wb+") as f:
            for chunk in data.chunks():
                f.write(chunk)
        thread = ImportThread(request.user.tj_email, import_dir)
        thread.start()
        context["completed"] = True
    return render(request, "eighth/admin/sis_import.html", context)


@eighth_admin_required
@reauthentication_required
def start_of_year_view(request):
    context = {"admin_page_title": "Start of Year Operations", "completed": False}
    if request.method == "POST" and request.POST.get("confirm"):
        try:
            content = StringIO()
            call_command("year_cleanup", run=True, confirm=True, stdout=content)
            content.seek(0)
            context["output"] = content.read()
        except Exception as e:
            # TODO: capture exception
            context["output"] = "An error occured while running the start of year scripts!\n\n{}".format(e)
        context["completed"] = True
    return render(request, "eighth/admin/start_of_year.html", context)


@eighth_admin_required
@reauthentication_required
def clear_comments_view(request):
    context = {"admin_page_title": "Clear Admin Comments", "completed": False}

    if request.method == "POST" and request.POST.get("confirm"):
        # TODO: delete admin comments when django models are made
        context["completed"] = True

    return render(request, "eighth/admin/clear_comments.html", context)
