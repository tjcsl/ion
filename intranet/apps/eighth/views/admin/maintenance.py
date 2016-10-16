# -*- coding: utf-8 -*-

import logging
import ldap3
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
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.management import call_command
from django.contrib import messages

from intranet.db.ldap_db import LDAPConnection

from cacheops import invalidate_obj

from ....auth.decorators import eighth_admin_required, reauthentication_required
from ....users.models import User

from ....notifications.emails import email_send

logger = logging.getLogger(__name__)

LDAP_STUDENT_FIELDS = [
    ("graduationYear", "Graduation Year")
]
LDAP_BASIC_FIELDS = [
    ("iodineUid", "Username"),
    ("iodineUidNumber", "User ID"),
    ("cn", "Full Name"),
    ("givenName", "First Name"),
    ("sn", "Last Name"),
    ("mail", "Email")
]
LDAP_DEFAULT_FIELDS = {
    "header": "TRUE",
    "style": "default",
    "chrome": "TRUE",
    "startpage": "news"
}


@eighth_admin_required
@reauthentication_required
def index_view(request):
    context = {
        "admin_page_title": "Maintenance Tools"
    }
    return render(request, "eighth/admin/maintenance.html", context)


@eighth_admin_required
@reauthentication_required
def ldap_management(request):
    context = {
        "admin_page_title": "LDAP Management",
        "fields": LDAP_BASIC_FIELDS,
        "default_fields": LDAP_DEFAULT_FIELDS,
        "student_fields": LDAP_STUDENT_FIELDS
    }
    return render(request, "eighth/admin/ldap_management.html", context)


def clear_user_cache(dn):
    user = User.get_user(dn=dn)
    invalidate_obj(user)
    user.clear_cache()


@eighth_admin_required
@reauthentication_required
def ldap_modify(request):
    dn = request.POST.get("dn", None)
    if request.method == "POST":
        c = LDAPConnection()

        object_class = request.POST.get("objectClass", None)
        if not object_class == "tjhsstStudent" and not object_class == "tjhsstTeacher":
            return JsonResponse({
                "success": False,
                "error": "Invalid objectClass!",
                "details": "Valid objectClasses are tjhsstStudent and tjhsstTeacher."
            })

        if dn:  # modify account
            attrs = {}
            for field, name in LDAP_BASIC_FIELDS:
                value = request.POST.get(field, None)
                if value:
                    attrs[field] = [(ldap3.MODIFY_REPLACE, [value])]

            if object_class == "tjhsstStudent":
                for field, name in LDAP_STUDENT_FIELDS:
                    value = request.POST.get(field, None)
                    if value:
                        attrs[field] = [(ldap3.MODIFY_REPLACE, [value])]

            success = c.conn.modify(dn, attrs)
            clear_user_cache(dn)
            new_uid = request.POST.get("iodineUid", None)
            if new_uid and not "iodineUid={},{}".format(new_uid, settings.USER_DN) == dn:
                success = success and c.conn.modify_dn(dn, "iodineUid={}".format(new_uid))
            return JsonResponse({
                "success": success,
                "id": new_uid if success else None,
                "error": "LDAP query failed!" if not success else None,
                "details": c.conn.last_error or str(c.conn.result)
            })
        else:  # create new account
            attrs = dict(LDAP_DEFAULT_FIELDS)
            for field, name in LDAP_BASIC_FIELDS:
                value = request.POST.get(field, None)
                if not value:
                    return JsonResponse({"success": False, "error": "{} is a required field!".format(field)})
                attrs[field] = value

            if object_class == "tjhsstStudent":
                for field, name in LDAP_STUDENT_FIELDS:
                    value = request.POST.get(field, None)
                    if not value:
                        return JsonResponse({"success": False, "error": "{} is a required field for students!".format(field)})
                    attrs[field] = value

            try:
                iodine_uid_num = int(attrs["iodineUidNumber"])
            except ValueError:
                return JsonResponse({"success": False, "error": "iodineUidNumber must be an integer!"})

            if object_class == "tjhsstTeacher":
                if iodine_uid_num < 0 or iodine_uid_num > 10000:
                    return JsonResponse({"success": False, "error": "iodineUidNumber must be between 0 and 10,000!"})
            else:
                if iodine_uid_num < 30000:
                    return JsonResponse({"success": False, "error": "iodineUidNumber must be above 30,000!"})

            success = c.conn.add("iodineUid={},{}".format(attrs["iodineUid"], settings.USER_DN), object_class=object_class, attributes=attrs)
            return JsonResponse({
                "success": success,
                "id": request.POST.get("iodineUid", None) if success else None,
                "error": "LDAP query failed!" if not success else None,
                "details": c.conn.last_error
            })
    return JsonResponse({"success": False})


@eighth_admin_required
@reauthentication_required
def ldap_delete(request):
    dn = request.POST.get("dn", None)
    if request.method == "POST" and dn:
        if not dn.endswith(settings.USER_DN):
            return JsonResponse({
                "success": False,
                "error": "Invalid DN!"
            })
        c = LDAPConnection()
        success = c.conn.delete(dn)
        clear_user_cache(dn)
        return JsonResponse({
            "success": success,
            "error": "LDAP query failed!" if not success else None,
            "details": c.conn.last_error
        })
    return JsonResponse({"success": False})


@eighth_admin_required
@reauthentication_required
def ldap_next_id(request):
    is_student = request.GET.get("type", "teacher") == "student"
    usrid = 0
    c = LDAPConnection()
    res = c.search(settings.USER_DN, "objectClass=tjhsstStudent" if is_student else "objectClass=tjhsstTeacher", ["iodineUidNumber"])
    if len(res) > 0:
        res = [int(x["attributes"]["iodineUidNumber"][0]) for x in res]
        if is_student:
            usrid = max(res) + 1
        else:
            res = set([x for x in res if x < 1200])
            usrid = max(res) + 1
            if usrid == 1200:
                for x in range(1200):
                    if x not in res:
                        usrid = x
                        break

    return JsonResponse({"id": usrid})


@eighth_admin_required
@reauthentication_required
def ldap_list(request):
    c = LDAPConnection()
    usrid = request.GET.get("id", None)
    if usrid:
        data = c.search(settings.USER_DN, "iodineUid={}".format(usrid), ["*"])
        if len(data) == 0:
            return JsonResponse({"account": None})
        account = {x: y[0] for x, y in data[0]["attributes"].items()}
        account["dn"] = data[0]["dn"]
        return JsonResponse({"account": account})
    else:
        is_student = request.GET.get("type", "teacher") == "student"
        data = c.search(settings.USER_DN, "objectClass=tjhsstStudent" if is_student else "objectClass=tjhsstTeacher", ["iodineUid", "cn"])
        accounts = [{"id": x["attributes"]["iodineUid"][0], "name": x["attributes"]["cn"][0]} for x in data]
        accounts = sorted(accounts, key=lambda acc: acc["name"])
        return JsonResponse({"accounts": accounts})


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
                    subprocess.check_call("ldapmodify", "-h", settings.LDAP_SERVER[7:], "-Y", "GSSAPI", "-f", f, env={
                        "KRB5CCNAME": os.environ["KRB5CCNAME"]
                    }, stdout=content, stderr=content)
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

        data = {
            "log": content.read(),
            "failure": failure,
            "help_email": settings.FEEDBACK_EMAIL,
            "date": start_time.strftime("%I:%M:%S %p %m/%d/%Y")
        }
        email_send("eighth/emails/import_notify.txt", "eighth/emails/import_notify.html", data, "SIS Import Results - {}".format("Failure" if failure else "Success"), [self.email])
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
    context = {
        "admin_page_title": "Start of Year Operations",
        "completed": False
    }
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
    context = {
        "admin_page_title": "Clear Admin Comments",
        "completed": False
    }
    if request.method == "POST" and request.POST.get("confirm"):
        deleted_comments = ""
        count = 0

        c = LDAPConnection()
        comments = c.search(settings.USER_DN, "objectClass=tjhsstStudent", ["eighthoffice-comments", "dn"])
        for row in comments:
            if "eighthoffice-comments" in row:
                c.del_attribute(row["dn"], "eighthoffice-comments")
                u = User.objects.get(dn=row["dn"])
                invalidate_obj(u)
                u.clear_cache()
                deleted_comments += "=== {} ({})\n{}\n".format(u.full_name, u.username, row["eighthoffice-comments"])
                count += 1

        context["deleted_comments"] = deleted_comments or "No comments were deleted."
        context["deleted_comments_count"] = count
        context["completed"] = True
    return render(request, "eighth/admin/clear_comments.html", context)
