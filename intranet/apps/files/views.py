# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import pysftp
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

    context = {
        "hosts": cred.HOSTS
    }
    return render(request, "files/home.html", context)

@login_required
def files_type(request, fstype=None):
    hosts = cred.HOSTS
    if fstype and fstype in hosts:
        host = hosts[fstype]
    else:
        messages.error(request, "Invalid host.")
        return redirect("files")


    sftp = create_session(host, cred.USER, cred.PASS)
    fsdir = request.GET.get("dir")

    if fsdir:
        sftp.chdir(fsdir)

    listdir = sftp.listdir()
    files = []
    for f in listdir:
        if not f.startswith("."):
            files.append(f)

    context = {
        "files": files,
        "cwd": sftp.pwd,
        "fs_type": "CSL filesystem"
    }

    return render(request, "files/home.html", context)

