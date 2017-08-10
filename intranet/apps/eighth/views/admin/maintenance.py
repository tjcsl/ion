# -*- coding: utf-8 -*-

import logging
import os
import threading
import shutil
import traceback
import subprocess
import datetime
import csv

from tempfile import gettempdir
from io import StringIO

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect
from django.core.management import call_command
from django.contrib import messages

from raven.contrib.django.raven_compat.models import client

from ....auth.decorators import eighth_admin_required, reauthentication_required

from ....notifications.emails import email_send

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

    def run(self):
        start_time = datetime.datetime.now()
        content = StringIO()
        failure = False

        try:
            content.write("=== Starting Import.\n\n")
            with open(os.path.join(self.folder, "data.csv"), "r") as f:
                reader = csv.reader(f)
                next(reader) # Skip header row
                for row in reader:
                    try:
                        u =  User.objects.get(student_id=row[0].strip())
                        u.first_name = row[3].strip()
                        u.last_name = row[2].strip()
                        u.middle_name = row[4].strip()
                        u.nickname = row[11].strip() if row[11].strip() != "" else None
                        u.gender = row[1].strip().upper() == "M"
                        u.graduation_year = settings.SENIOR_GRADUATION_YEAR - int(row[5].strip()) + 12
                        props = u.properties
                        if props._address:
                            props._address.delete()
                        props._address = Address.objects.create(street=row[6].strip(), city=row[7].strip(), state=row[8].strip(), postal_code=row[9].strip())
                        birthday_values = row[12].strip().split("/")
                        props._birthday = "{}-{}-{}".format(birthday_values[2], birthday_values[0], birthday_values[1])
                        props.save()
                        u.save()
                        content.write("Updated information for {}\n".format(u.username))
                    except User.DoesNotExist:
                        if row[10].strip() == "":
                            content.write("Skipping {}, no username available and user does not exist in database\n".format(row))
                        u = User.objects.create(username=row[10].strip().lower(), student_id=row[0].strip())
                        u.first_name = row[3].strip()
                        u.last_name = row[2].strip()
                        u.middle_name = row[4].strip()
                        u.nickname = row[11].strip() if row[11].strip() != "" else None
                        u.gender = row[1].strip().upper() == "M"
                        u.graduation_year = settings.SENIOR_GRADUATION_YEAR - int(row[5].strip()) + 12
                        props = u.properties
                        if props._address:
                            props._address.delete()
                        props._address = Address.objects.create(street=row[6].strip(), city=row[7].strip(), state=row[8].strip(), postal_code=row[9].strip())
                        birthday_values = row[12].strip().split("/")
                        props._birthday = "{}-{}-{}".format(birthday_values[2], birthday_values[0], birthday_values[1])
                        props.save()
                        u.save()
                        content.write("User {} did not exist in database - created and updated information\n".format(u.username))
            content.write("\n\n==== Successfully completed SIS Import\n\n")
        except Exception:
            failure = True
            content.write("\n=== An error occured during the import process!\n\n")
            content.write(traceback.format_exc())
            content.write("\n=== The import process has been aborted.")

        content.seek(0)

        data = {"log": content.read(), "failure": failure, "help_email": settings.FEEDBACK_EMAIL, "date": start_time.strftime("%I:%M:%S %p %m/%d/%Y")}
        email_send("eighth/emails/import_notify.txt", "eighth/emails/import_notify.html", data,
                   "SIS Import Results - {}".format("Failure" if failure else "Success"), [self.email])
        shutil.rmtree(self.folder)


@eighth_admin_required
@reauthentication_required
def sis_import(request):
    import_dir = get_import_directory()
    context = {
        "admin_page_title": "SIS Import",
        "email": request.user.tj_email,
        "help_email": settings.FEEDBACK_EMAIL,
        "already_importing": os.path.isdir(import_dir),
        "completed": False
    }
    if request.method == "POST":
        if context["already_importing"]:
            messages.error(request, "An upload is currently in progress!")
            return redirect(reverse("eighth_admin_maintenance_sis_import"))
        if len(request.FILES) == 0:
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
            client.captureException()
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
