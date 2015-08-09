# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import pysftp
import tempfile
import os
import base64
from os.path import normpath
from Crypto import Random
from Crypto.Cipher import AES
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from .models import Host
from .forms import UploadFileForm
from intranet import settings

logger = logging.getLogger(__name__)

def create_session(hostname, username, password):
    return pysftp.Connection(hostname, username=username, password=password)

@login_required
def files_view(request):
    """The main filecenter view."""
    if not request.user.has_admin_permission('files'):
        return render(request, "files/devel_message.html")


    hosts = Host.objects.visible_to_user(request.user)

    context = {
        "hosts": hosts
    }
    return render(request, "files/home.html", context)

@login_required
def files_auth(request):
    """Display authentication for filecenter."""
    if "password" in request.POST:
        """
            Encrypt the password with AES mode CFB.
            Create a random 32 char key, stored in a CLIENT-side cookie.
            Create a random 32 char IV, stored in a SERVER-side session.
            Store the encrypted ciphertext in a SERVER-side session.

            This ensures that neither side can decrypt the password without
            the information stored on the other end of the request.

            Both the server-side session variables and the client-side cookies
            are deleted when the user logs out.
        """
        key = Random.new().read(32)
        iv = Random.new().read(16)
        obj = AES.new(key, AES.MODE_CFB, iv)
        message = request.POST.get("password")
        ciphertext = obj.encrypt(message)
        request.session["files_iv"] = base64.b64encode(iv)
        request.session["files_text"] = base64.b64encode(ciphertext)
        cookie_key = base64.b64encode(key)

        nexturl = request.GET.get("next", None)
        if nexturl and nexturl.startswith("/files"):
            response = redirect(nexturl)
        else:
            response = redirect("files")
        response.set_cookie(key="files_key", value=cookie_key)
        return response
    else:
        return render(request, "files/auth.html", {})


def get_authinfo(request):
    """Get authentication info from the encrypted message.
    """
    if (("files_iv" not in request.session) or 
        ("files_text" not in request.session) or 
        ("files_key" not in request.COOKIES)):
        return False

    """
        Decrypt the password given the SERVER-side IV, SERVER-side
        ciphertext, and CLIENT-side key.

        See note above on why this is done.
    """

    iv = base64.b64decode(request.session["files_iv"])
    text = base64.b64decode(request.session["files_text"])
    key = base64.b64decode(request.COOKIES["files_key"])

    obj = AES.new(key, AES.MODE_CFB, iv)
    password = obj.decrypt(text)

    return {
        "username": request.user.username,
        "password": password
    }

def windows_dir_format(host_dir, user):
    """Format a string for the location of the user's folder on the
       Windows (TJ03) fileserver.
    """
    grade_folders = {
        9: "Freshman M:",
        10: "Sophomore M:",
        11: "Junior M:",
        12: "Senior M:"
    }
    grade = int(user.grade)
    if grade in range(9, 13):
        win_path = "{}/{}/".format(grade_folders[grade], user.username)
    else:
        win_path = ""
    return host_dir.replace("{win}", win_path)

@login_required
def files_type(request, fstype=None):
    """Do all processing (directory listing, file downloads) for a
       given filesystem.
    """
    try:
        host = Host.objects.get(code=fstype)
    except Host.DoesNotExist:
        messages.error(request, "Could not find host in database.")
        return redirect("files")

    if not host.visible_to(request.user):
        messages.error(request, "You don't have permission to access this host.")
        return redirect("files")

    authinfo = get_authinfo(request)

    if not authinfo:
        return redirect("{}?next={}".format(reverse("files_auth"), request.get_full_path()))

    try:
        sftp = create_session(host.address, authinfo["username"], authinfo["password"])
    except pysftp.SSHException as e:
        messages.error(request, e)
        error_msg = str(e).lower()
        if "authentication" in error_msg:
            return redirect("files_auth")
        return redirect("files")
    else:
        # Delete the stored credentials, so they aren't mistakenly used or accessed later.
        authinfo = None
        del authinfo

    if host.directory:
        host_dir = host.directory
        if "{}" in host_dir:
            host_dir = host_dir.format(authinfo["username"])
        if "{win}" in host_dir:
            host_dir = windows_dir_format(host_dir, request.user)
        try:
            sftp.chdir(host_dir)
        except IOError as e:
            messages.error(request, e)
            return redirect("files")

    default_dir = sftp.pwd

    def can_access_path(fsdir):
        return normpath(fsdir).startswith(default_dir)


    if "file" in request.GET:
        # Download file
        filepath = request.GET.get("file")
        filepath = normpath(filepath)
        filebase = os.path.basename(filepath)
        if can_access_path(filepath):
            try:
                stat = sftp.stat(filepath)
            except:
                messages.error(request, "Unable to access {}".format(filebase))
                return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

            if stat.st_size > settings.FILES_MAX_DOWNLOAD_SIZE:
                messages.error(request, "Too large to download (>200MB)")
                return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

            tmpfile = tempfile.TemporaryFile(prefix="ion_{}_{}".format(request.user.username, filebase))
            logger.debug(tmpfile)

            try:
                sftp.getfo(filepath, tmpfile)
            except IOError as e:
                messages.error(request, e)
                return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

            content_len = tmpfile.tell()
            tmpfile.seek(0)
            chunk_size = 8192
            response = StreamingHttpResponse(FileWrapper(tmpfile, chunk_size), content_type="application/octet-stream")
            response['Content-Length'] = content_len
            response["Content-Disposition"] = "attachment; filename={}".format(filebase)
            return response

    fsdir = request.GET.get("dir")
    if fsdir:
        fsdir = normpath(fsdir)
        if can_access_path(fsdir):
            try:
                sftp.chdir(fsdir)
            except IOError as e:
                messages.error(request, e)
                return redirect("files")
        else:
            messages.error(request, "Access to the path you provided is restricted.")
            return redirect("/files/{}/?dir={}".format(fstype, default_dir))

    try:
        listdir = sftp.listdir()
    except IOError as e:
        messages.error(request, e)
        listdir = []
    files = []
    for f in listdir:
        if not f.startswith("."):
            try:
                stat = sftp.stat(f)
            except:
                # If we can't stat the file, don't show it
                continue
            files.append({
                "name": f,
                "folder": sftp.isdir(f),
                "stat": stat,
                "too_big": stat.st_size > settings.FILES_MAX_DOWNLOAD_SIZE
            })



    current_dir = sftp.pwd # current directory
    dir_list = current_dir.split("/")
    if len(dir_list) > 1 and len(dir_list[-1]) == 0:
        dir_list.pop()
    parent_dir = "/".join(dir_list[:-1])

    if len(parent_dir) == 0:
        parent_dir = "/"

    files = sorted(files, key=lambda f: (not f["folder"], f["name"]))

    context = {
        "host": host,
        "files": files,
        "current_dir": current_dir,
        "parent_dir": parent_dir if can_access_path(parent_dir) else None,
        "max_download_mb": (settings.FILES_MAX_DOWNLOAD_SIZE / 1024 / 1024)
    }

    return render(request, "files/directory.html", context)

@login_required
def files_upload(request, fstype=None):
    fsdir = request.GET.get("dir", None)
    if fsdir is None:
        return redirect("files")

    try:
        host = Host.objects.get(code=fstype)
    except Host.DoesNotExist:
        messages.error(request, "Could not find host in database.")
        return redirect("files")

    if not host.visible_to(request.user):
        messages.error(request, "You don't have permission to access this host.")
        return redirect("files")

    authinfo = get_authinfo(request)

    if not authinfo:
        return redirect("{}?next={}".format(reverse("files_auth"), request.get_full_path()))


    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                sftp = create_session(host.address, authinfo["username"], authinfo["password"])
            except pysftp.SSHException as e:
                messages.error(request, e)
                return redirect("files")
            else:
                # Delete the stored credentials, so they aren't mistakenly used or accessed later.
                authinfo = None
                del authinfo

            if host.directory:
                host_dir = host.directory
                if "{}" in host_dir:
                    host_dir = host_dir.format(authinfo["username"])
                if "{win}" in host_dir:
                    host_dir = windows_dir_format(host_dir, request.user)
                try:
                    sftp.chdir(host_dir)
                except IOError as e:
                    messages.error(request, e)
                    return redirect("files")

            default_dir = sftp.pwd

            def can_access_path(fsdir):
                return normpath(fsdir).startswith(default_dir)

            fsdir = normpath(fsdir)
            if not can_access_path(fsdir):
                messages.error(request, "Access to the path you provided is restricted.")
                return redirect("/files/{}/?dir={}".format(fstype, default_dir))

            handle_file_upload(request.FILES['file'], fstype, fsdir, sftp, request)
            return redirect("/files/{}/?dir={}".format(fstype, fsdir))
    else:
        form = UploadFileForm()
    context = {
        "host": host,
        "remote_dir": fsdir,
        "form": form,
        "max_upload_mb": (settings.FILES_MAX_UPLOAD_SIZE / 1024 / 1024)
    }
    return render(request, "files/upload.html", context)

def handle_file_upload(file, fstype, fsdir, sftp, request=None):
    try:
        sftp.chdir(fsdir)
    except IOError as e:
        messages.error(request, e)
        return

    remote_path = "{}/{}".format(fsdir, file.name)
    try:
        sftp.putfo(file, remote_path)
    except IOError as e:
        # Remote path does not exist
        messages.error(request, e)
        return
    except OSError as e:
        messages.error(request, "Unable to upload: {}".format(e))
        return


    messages.success(request, "Uploaded {} to {}".format(file.name, fsdir))
