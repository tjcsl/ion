# -*- coding: utf-8 -*-

import logging
import os
import threading
import shutil
import traceback
import subprocess
import datetime

from tempfile import gettempdir
from io import StringIO

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect
from django.core.management import call_command
from django.contrib import messages

from cacheops import invalidate_obj

from ....auth.decorators import eighth_admin_required, reauthentication_required
from ....users.models import User

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
            content.write("=== Starting CSV to LDIF script.\n\n")
            os.chdir(self.folder)
            call_command("import_sis", csv_file=os.path.join(self.folder, "data.csv"), run=True, confirm=True, stdout=content, stderr=content)
            content.write("\n=== Finished CSV to LDIF script.\n")

            content.write("=== Starting LDIF import.\n")
            ldifs_imported = 0
            for f in os.listdir(self.folder):
                if f.endswith(".ldif"):
                    content.write("=== Importing {}\n".format(f))
                    # ldap3 does not support importing LDIF files
                    subprocess.check_call("ldapmodify", "-h", settings.LDAP_SERVER[7:], "-Y", "GSSAPI", "-f", f,
                                          env={"KRB5CCNAME": os.environ["KRB5CCNAME"]}, stdout=content, stderr=content)
                    content.write("=== Imported {}\n".format(f))
                    ldifs_imported += 1
            if ldifs_imported == 0:
                content.write("=== WARNING: No LDIF files were imported!\n")
                failure = True
            else:
                content.write("=== {} LDIF files were imported.\n".format(ldifs_imported))
            content.write("=== Finished LDIF import.\n")

            content.write("Processing complete.\n")
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
        content = StringIO()
        call_command("year_cleanup", run=True, confirm=True, stdout=content)
        content.seek(0)
        context["output"] = content.read()
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
