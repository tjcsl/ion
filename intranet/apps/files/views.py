# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import pysftp
import tempfile
import os
from os.path import normpath
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.core.servers.basehttp import FileWrapper
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
        "csl": "Computer Systems Lab",
        "win": "Windows/LOCAL"
    }

    context = {
        "hosts_desc": hosts_desc
    }
    return render(request, "files/home.html", context)

@login_required
def files_type(request, fstype=None):
    hosts = cred.HOSTS
    hosts_desc = {
        "csl": "Computer Systems Lab",
        "win": "Windows/LOCAL"
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
        filebase = os.path.basename(filepath)
        if can_access_path(filepath):
            tmpfile = tempfile.NamedTemporaryFile(prefix="ion_{}_{}".format(request.user.username, filebase))
            tmppath = tmpfile.name
            logger.debug(tmpfile)
            logger.debug(tmppath)
            sftp.get(filepath, localpath=tmppath)
            try:
                tmpopen = open(tmppath)
            except IOError:
                messages.error(request, "Unable to download {}".format(filebase))
                return redirect("/files/{}/?dir={}".format(fstype, os.path.dirname(filepath)))
            else:
                chunk_size = 8192
                response = StreamingHttpResponse(FileWrapper(tmpopen, chunk_size), content_type="application/octet-stream")
                response['Content-Length'] = os.path.getsize(tmppath)
                response["Content-Disposition"] = "attachment; filename={}".format(filebase)
                return response

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

