# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import pysftp
import tempfile
import os
from os.path import normpath
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from . import cred

logger = logging.getLogger(__name__)


def create_session(hostname, username, password):
    return pysftp.Connection(hostname, username=username, password=password)

@login_required
def files_view(request):
    """The main filecenter view."""
    if not request.user.has_admin_permission('files'):
        return render(request, "files/devel_message.html")


    hosts_desc = {
        "csl": "Computer Systems Lab Filesystem",
        "win": "Windows Filesystem"
    }

    context = {
        "hosts_desc": hosts_desc
    }
    return render(request, "files/home.html", context)

@login_required
def files_type(request, fstype=None):
    hosts = cred.HOSTS
    hosts_desc = {
        "csl": "Computer Systems Lab Filesystem",
        "win": "Windows Filesystem"
    }
    if fstype and fstype in hosts:
        host = hosts[fstype]
    else:
        messages.error(request, "Invalid host.")
        return redirect("files")

    try:
        sftp = create_session(host, cred.USER, cred.PASS)
    except pysftp.SSHException as e:
        messages.error(request, e)
        return redirect("files")


    default_dir = sftp.pwd

    def can_access_path(fsdir):
        #if request.user.has_admin_permission('files'):
        #    return True
        return normpath(fsdir).startswith(default_dir)


    if "file" in request.GET:
        # Download file
        filepath = request.GET.get("file")
        filepath = normpath(filepath)
        if can_access_path(filepath):
            tmpdir = tempfile.mkdtemp(prefix="ion_{}".format(request.user.username))
            sftp.get(filepath, localpath=tmpdir)
            files = os.listdir(tmpdir)
            logger.debug(files)
            if len(files) == 1:
                tmppath = "{}/{}".format(tmpdir, files[0])
                logger.debug(tmppath)
                basename = os.path.basename(tmppath)
                tmpfile = open(tmppath, "r")
                response = HttpResponse(FileWrapper(tmpfile.read()), content_type="application/octet-stream")
                response["Content-Disposition"] = "attachment; filename={}".format(basename)
                return response
            else:
                messages.error(request, "An error occurred downloading the file.")
                return redirect("/files/{}/?dir={}".format(fstype, os.path.dirname(filepath)))

    fsdir = request.GET.get("dir")
    if fsdir:
        fsdir = normpath(fsdir)
        if can_access_path(fsdir):
            sftp.chdir(fsdir)
        else:
            messages.error(request, "Access to the path you provided is restricted.")
            return redirect("/files/{}/?dir={}".format(fstype, default_dir))

    listdir = sftp.listdir()
    files = []
    for f in listdir:
        if not f.startswith("."):
            files.append({
                "name": f,
                "folder": sftp.isdir(f),
            })

    current_dir = sftp.pwd # current directory
    dir_list = current_dir.split("/")
    parent_dir = "/".join(dir_list[:-1])

    context = {
        "files": files,
        "current_dir": current_dir,
        "parent_dir": parent_dir if can_access_path(parent_dir) else None,
        "fs_type": hosts_desc[fstype]
    }

    return render(request, "files/directory.html", context)

