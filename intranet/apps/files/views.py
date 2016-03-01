# -*- coding: utf-8 -*-

import base64
import datetime
import logging
import os
import stat
import tempfile
import zipfile
from os.path import normpath
from wsgiref.util import FileWrapper

from Crypto import Random
from Crypto.Cipher import AES

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import (sensitive_post_parameters, sensitive_variables)

import pysftp

from .forms import UploadFileForm
from .models import Host

logger = logging.getLogger(__name__)


def create_session(hostname, username, password):
    return pysftp.Connection(hostname, username=username, password=password)


@login_required
def files_view(request):
    """The main filecenter view."""

    hosts = Host.objects.visible_to_user(request.user)

    context = {"hosts": hosts}
    return render(request, "files/home.html", context)


@login_required
@sensitive_variables('message', 'key', 'iv', 'ciphertext')
@sensitive_post_parameters('password')
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
        request.session["files_iv"] = base64.b64encode(iv).decode()
        request.session["files_text"] = base64.b64encode(ciphertext).decode()
        cookie_key = base64.b64encode(key).decode()

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
    """Get authentication info from the encrypted message."""
    if (("files_iv" not in request.session) or ("files_text" not in request.session) or ("files_key" not in request.COOKIES)):
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

    return {"username": request.user.username, "password": password}


def windows_dir_format(host_dir, user):
    """Format a string for the location of the user's folder on the Windows (TJ03) fileserver."""
    grade_folders = {9: "Freshman M:", 10: "Sophomore M:", 11: "Junior M:", 12: "Senior M:"}
    if user and user.grade:
        grade = int(user.grade)
    else:
        return host_dir

    if grade in range(9, 13):
        win_path = "{}/{}/".format(grade_folders[grade], user.username)
    else:
        win_path = ""
    return host_dir.replace("{win}", win_path)


@login_required
def files_type(request, fstype=None):
    """Do all processing (directory listing, file downloads) for a given filesystem."""
    try:
        host = Host.objects.get(code=fstype)
    except Host.DoesNotExist:
        messages.error(request, "Could not find host in database.")
        return redirect("files")

    if host.available_to_all:
        pass
    elif not host.visible_to(request.user):
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
    finally:
        # Delete the stored credentials, so they aren't mistakenly used or accessed later.
        del authinfo

    if host.directory:
        host_dir = host.directory
        if "{}" in host_dir:
            host_dir = host_dir.format(request.user.username)
        if "{win}" in host_dir:
            host_dir = windows_dir_format(host_dir, request.user)
            try:
                sftp.chdir(host_dir)
            except IOError as e:
                if "NoSuchFile" in "{}".format(e):
                    host_dir = "/"
                    try:
                        sftp.chdir(host_dir)
                    except IOError as e2:
                        messages.error(request, e)
                        messages.error(request, "Root directory: {}".format(e2))
                        return redirect("files")
                    else:
                        messages.error(request, "Unable to access home folder -- showing root directory instead.")
                else:
                    messages.error(request, e)
                    return redirect("files")
        else:
            try:
                sftp.chdir(host_dir)
            except IOError as e:
                messages.error(request, e)
                return redirect("files")

    default_dir = normpath(sftp.pwd)

    def can_access_path(fsdir):
        return normpath(fsdir).startswith(default_dir)

    if "file" in request.GET:
        # Download file
        filepath = request.GET.get("file")
        filepath = normpath(filepath)
        filebase = os.path.basename(filepath)
        filebase_escaped = filebase.replace(",", "")
        filebase_escaped = filebase_escaped.encode("ascii", "ignore").decode()
        if can_access_path(filepath):
            try:
                fstat = sftp.stat(filepath)
            except:
                messages.error(request, "Unable to access {}".format(filebase))
                return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

            if fstat.st_size > settings.FILES_MAX_DOWNLOAD_SIZE:
                messages.error(request, "Too large to download (>200MB)")
                return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

            tmpfile = tempfile.TemporaryFile(prefix="ion_filecenter_{}_{}".format(request.user.username, filebase_escaped))
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
            response["Content-Disposition"] = "attachment; filename={}".format(filebase_escaped)
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

    if "zip" in request.GET:
        dirbase_escaped = os.path.basename(fsdir).replace(",", "")
        dirbase_escaped = dirbase_escaped.encode("ascii", "ignore").decode()
        tmpfile = tempfile.TemporaryFile(prefix="ion_filecenter_{}_{}".format(request.user.username, dirbase_escaped))

        with tempfile.TemporaryDirectory(prefix="ion_filecenter_{}_{}_zip".format(request.user.username, dirbase_escaped)) as tmpdir:
            remote_directories = [fsdir]
            totalsize = 0
            while remote_directories:
                rd = remote_directories.pop()
                remotelist = sftp.listdir(rd)
                for item in remotelist:
                    itempath = os.path.join(rd, item)
                    try:
                        fstat = sftp.stat(itempath)
                    except:
                        logger.debug("Could not read " + item)
                        continue

                    if stat.S_ISDIR(fstat.st_mode):
                        remote_directories.append(itempath)
                        continue

                    totalsize += fstat.st_size
                    if totalsize > settings.FILES_MAX_DOWNLOAD_SIZE:
                        messages.error(request, "Too large to download (>200MB)")
                        return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(fsdir)))

                    try:
                        localpath = os.path.join(tmpdir, os.path.relpath(rd, fsdir))
                        if not os.path.exists(localpath):
                            os.makedirs(localpath)
                        fh = open(os.path.join(localpath, item), "wb")
                        sftp.getfo(itempath, fh)
                    except IOError as e:
                        logger.debug("IOError on " + item)
                        continue

            with zipfile.ZipFile(tmpfile, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(tmpdir):
                    for f in files:
                        zf.write(os.path.join(root, f), os.path.join(os.path.relpath(root, tmpdir), f))

        content_len = tmpfile.tell()
        tmpfile.seek(0)
        chunk_size = 8192
        response = StreamingHttpResponse(FileWrapper(tmpfile, chunk_size), content_type="application/octet-stream")
        response["Content-Length"] = content_len
        response["Content-Disposition"] = "attachment; filename={}".format(dirbase_escaped + ".zip")
        return response

    try:
        listdir = sftp.listdir()
    except IOError as e:
        messages.error(request, e)
        listdir = []
    files = []
    for f in listdir:
        if not f.startswith("."):
            try:
                fstat = sftp.stat(f)
            except:
                # If we can't stat the file, don't show it
                continue
            files.append({
                "name": f,
                "folder": sftp.isdir(f),
                "stat": fstat,
                "stat_mtime": datetime.datetime.fromtimestamp(int(fstat.st_mtime or 0)),
                "too_big": fstat.st_size > settings.FILES_MAX_DOWNLOAD_SIZE
            })

    logger.debug(files)

    current_dir = normpath(sftp.pwd)  # current directory
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
def files_delete(request, fstype=None):
    if "confirm" in request.POST:
        filepath = request.POST.get("path", None)
    else:
        filepath = request.GET.get("dir", None)
    if filepath is None:
        return redirect("files")

    try:
        host = Host.objects.get(code=fstype)
    except Host.DoesNotExist:
        messages.error(request, "Could not find host in database.")
        return redirect("files")

    if host.available_to_all:
        pass
    elif not host.visible_to(request.user):
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
    finally:
        # Delete the stored credentials, so they aren't mistakenly used or accessed later.
        del authinfo

    if host.directory:
        host_dir = host.directory
        if "{}" in host_dir:
            host_dir = host_dir.format(request.user.username)
        if "{win}" in host_dir:
            host_dir = windows_dir_format(host_dir, request.user)
        try:
            sftp.chdir(host_dir)
        except IOError as e:
            messages.error(request, e)
            return redirect("files")

    default_dir = normpath(sftp.pwd)

    def can_access_path(fsdir):
        return normpath(fsdir).startswith(default_dir)

    filepath = normpath(filepath)
    if can_access_path(filepath):
        try:
            fstat = sftp.stat(filepath)
            is_directory = stat.S_ISDIR(fstat.st_mode)
        except:
            messages.error(request, "Unable to access {}".format(filepath))
            return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

    def rmtree(sftp, path):
        for f in sftp.listdir_attr(path):
            npath = os.path.join(path, f.filename)
            if stat.S_ISDIR(f.st_mode):
                rmtree(sftp, npath)
            else:
                sftp.remove(npath)
        sftp.rmdir(path)

    if "confirm" in request.POST:
        try:
            if is_directory:
                rmtree(sftp, filepath)
            else:
                sftp.remove(filepath)
            messages.success(request, ("Folder" if is_directory else "File") + " deleted!")
        except PermissionError:
            messages.error(request, "You are not allowed to delete this " + ("folder" if is_directory else "file") + "!")
        return redirect("/files/{}?dir={}".format(fstype, os.path.dirname(filepath)))

    context = {
        "host": host,
        "remote_dir": os.path.dirname(filepath),
        "is_directory": is_directory
    }
    return render(request, "files/delete.html", context)


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
    if host.available_to_all:
        pass
    elif not host.visible_to(request.user):
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

            default_dir = normpath(sftp.pwd)

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
    context = {"host": host, "remote_dir": fsdir, "form": form, "max_upload_mb": (settings.FILES_MAX_UPLOAD_SIZE / 1024 / 1024)}
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
