# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import magic
import os
import subprocess
import tempfile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from intranet import settings
from .models import PrintJob
from .forms import PrintJobForm

logger = logging.getLogger(__name__)


def get_printers():
    proc = subprocess.Popen(["lpstat", "-a"], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    lines = output.split("\n")
    logger.debug(lines)
    names = []
    for l in lines:
        if "requests since" in l:
            names.append(l.split(" ")[0])

    if "Please_Select_a_Printer" in names:
        names.remove("Please_Select_a_Printer")

    if "" in names:
        names.remove("")

    return names

def get_file_string(fileobj):
    filetext = ""
    for chunk in fileobj.chunks():
        filetext += unicode(chunk, "ISO-8859-1")
    return filetext

def convert_soffice(tmpfile_name):
    proc = subprocess.Popen(["soffice", "--headless", "--convert-to", "pdf", tmpfile_name, "--outdir", "/tmp"], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    if err:
        return False

    if " -> " in output and " using " in output:
        fileout = output.split(" -> ")[1]
        fileout = fileout.split(" using ")[0]
        return fileout

    return False

def convert_file(tmpfile_name):
    mime = magic.Magic(mime=True)
    detected = mime.from_file(tmpfile_name)
    NO_CONVERSION = [
        "application/pdf",
        "application/postscript"
    ]
    SOFFICE_CONVERT = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]
    if detected in NO_CONVERSION:
        return tmpfile_name

    # .docx
    if detected in SOFFICE_CONVERT:
        return convert_soffice(tmpfile_name)

    return Exception("Not sure how to handle a file of type {}".format(detected))

def print_job(obj):
    logger.debug(obj)

    printer = obj.printer
    if printer not in get_printers():
        return Exception("Printer not authorized.")

    if not obj.file:
        return Exception("No file.")


    fileobj = obj.file

    filebase = os.path.basename(fileobj.name)
    filebase_escaped = filebase.encode("ascii", "ignore")
    filebase_escaped = filebase_escaped.replace(",", "")
    tmpfile_name = tempfile.NamedTemporaryFile(prefix="ion_print_{}_{}".format(obj.user.username, filebase_escaped)).name

    with open(tmpfile_name, 'wb+') as dest:
        for chunk in fileobj.chunks():
            dest.write(chunk)

    logger.debug(tmpfile_name)

    tmpfile_name = convert_file(tmpfile_name)
    logger.debug(tmpfile_name)
    
    if not tmpfile_name:
        return Exception("Could not convert file.")

    proc = subprocess.Popen(["lpr", "-P", "{}".format(printer), "{}".format(tmpfile_name)], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()

@login_required
def print_view(request):
    printers = get_printers()
    if request.method == "POST":
        form = PrintJobForm(request.POST, request.FILES, printers=printers)
        if form.is_valid():
            obj = form.save(commit=True)
            obj.user = request.user
            obj.save()
            try:
                print_job(obj)
            except Exception as e:
                messages.error(request, "{}".format(e))
            else:
                messages.success(request, "Your file was printed!")
    else:
        form = PrintJobForm(printers=printers)
    context = {
        "form": form
    }
    return render(request, "printing/print.html", context)