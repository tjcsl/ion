# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

import magic

from .forms import PrintJobForm
from ..context_processors import _get_current_ip

logger = logging.getLogger(__name__)


def get_printers():
    proc = subprocess.Popen(["lpstat", "-a"], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    output = output.decode()
    lines = output.split("\n")
    names = []
    for l in lines:
        if "requests since" in l:
            names.append(l.split(" ")[0])

    if "Please_Select_a_Printer" in names:
        names.remove("Please_Select_a_Printer")

    if "" in names:
        names.remove("")

    return names


def convert_soffice(tmpfile_name):
    proc = subprocess.Popen(["soffice", "--headless", "--convert-to", "pdf", tmpfile_name, "--outdir", "/tmp"], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    if err:
        return False

    output = output.decode()

    if " -> " in output and " using " in output:
        fileout = output.split(" -> ")[1]
        fileout = fileout.split(" using ")[0]
        return fileout

    return False


def convert_pdf(tmpfile_name, cmdname="ps2pdf"):
    new_name = "{}.pdf".format(tmpfile_name)
    proc = subprocess.Popen([cmdname, tmpfile_name, new_name], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    output = output.decode()

    if err:
        return False

    if os.path.isfile(new_name):
        return new_name

    return False


def get_numpages(tmpfile_name):
    proc = subprocess.Popen(["pdfinfo", tmpfile_name], stdout=subprocess.PIPE)
    (output, err) = proc.communicate()
    if err:
        return False

    output = output.decode()
    lines = output.split("\n")
    num_pages = -1
    for l in lines:
        if l.startswith("Pages:"):
            try:
                num_pages = l.split("Pages:")[1].strip()
                num_pages = int(num_pages)
            except Exception:
                num_pages = -1

    return num_pages


def convert_file(tmpfile_name):
    mime = magic.Magic(mime=True)
    detected = mime.from_file(tmpfile_name)
    detected = detected.decode()
    no_conversion = ["application/pdf", "text/plain"]
    soffice_convert = ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword",
                       "application/vnd.oasis.opendocument.text"]
    if detected in no_conversion:
        return tmpfile_name

    # .docx
    if detected in soffice_convert:
        return convert_soffice(tmpfile_name)

    if detected == "application/postscript":
        return convert_pdf(tmpfile_name, "pdf2ps")

    raise Exception("Not sure how to handle a file of type {}".format(detected))


def check_page_range(page_range, max_pages):
    """ Returns the number of pages in the range, or False if it is an invalid range. """
    pages = 0
    try:
        for r in page_range.split(","):  # check all ranges separated by commas
            if "-" in r:
                rr = r.split("-")
                if not len(rr) == 2:  # make sure 2 values in range
                    return False
                else:
                    rl = int(rr[0])
                    rh = int(rr[1])
                    if not 0 < rl < max_pages and not 0 < rh < max_pages:  # check in page range
                        return False
                    if rl > rh:   # check lower bound <= upper bound
                        return False
                    pages += rh - rl + 1
            else:
                if not 0 < int(r) <= max_pages:  # check in page range
                    return False
                pages += 1
    except ValueError:  # catch int parse fail
        return False
    return pages


def print_job(obj, do_print=True):
    logger.debug(obj)

    printer = obj.printer
    if printer not in get_printers():
        return Exception("Printer not authorized.")

    if not obj.file:
        return Exception("No file.")

    fileobj = obj.file

    filebase = os.path.basename(fileobj.name)
    filebase_escaped = filebase.replace(",", "")
    filebase_escaped = filebase_escaped.encode("ascii", "ignore")
    filebase_escaped = filebase_escaped.decode()
    tmpfile_name = tempfile.NamedTemporaryFile(prefix="ion_print_{}_{}".format(obj.user.username, filebase_escaped)).name

    with open(tmpfile_name, 'wb+') as dest:
        for chunk in fileobj.chunks():
            dest.write(chunk)

    logger.debug(tmpfile_name)

    tmpfile_name = convert_file(tmpfile_name)
    logger.debug(tmpfile_name)

    if not tmpfile_name:
        raise Exception("Could not convert file.")

    num_pages = get_numpages(tmpfile_name)
    obj.num_pages = num_pages
    obj.page_range = "".join(obj.page_range.split())  # remove all spaces
    obj.save()

    range_count = check_page_range(obj.page_range, obj.num_pages)

    if obj.page_range:
        if not range_count:
            raise Exception("You specified an invalid page range.")
        elif range_count > settings.PRINTING_PAGES_LIMIT:
            raise Exception("You specified a range of {} pages. You may only print up to {} pages using this tool.".format(range_count,
                                                                                                                           settings.PRINTING_PAGES_LIMIT))
    elif num_pages > settings.PRINTING_PAGES_LIMIT:
        raise Exception("This file contains {} pages. You may only print up to {} pages using this tool.".format(num_pages,
                                                                                                                 settings.PRINTING_PAGES_LIMIT))

    obj.printed = True
    obj.save()
    if do_print:
        args = ["lpr", "-P", "{}".format(printer), "{}".format(tmpfile_name)]
        if obj.page_range:
            args.extend(["-o", "page-ranges={}".format(obj.page_range)])
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        (output, err) = proc.communicate()


@login_required
def print_view(request):
    if _get_current_ip(request) not in settings.TJ_IPS and not request.user.has_admin_permission("printing"):
        messages.error(request, "You don't have printer access outside of the TJ network.")
        return redirect("index")

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
    context = {"form": form}
    return render(request, "printing/print.html", context)
