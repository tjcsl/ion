# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.text import slugify

import magic

from .forms import PrintJobForm
from ..context_processors import _get_current_ip

logger = logging.getLogger(__name__)


def get_printers():
    try:
        output = subprocess.check_output(["lpstat", "-a"], universal_newlines=True)
    # Don't die if cups isn't installed.
    except FileNotFoundError:
        return []
    lines = output.splitlines()
    names = []
    for l in lines:
        if "requests since" in l:
            names.append(l.split(" ", 1)[0])

    if "Please_Select_a_Printer" in names:
        names.remove("Please_Select_a_Printer")

    if "" in names:
        names.remove("")

    return names


def convert_soffice(tmpfile_name):
    try:
        output = subprocess.check_output(["soffice", "--headless", "--convert-to", "pdf", tmpfile_name, "--outdir", "/tmp"], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logger.error("Could not run soffice command (returned {}): {}".format(e.returncode, e.output))
        return False

    if " -> " in output and " using " in output:
        fileout = output.split(" -> ", 2)[1]
        fileout = fileout.split(" using ", 1)[0]
        return fileout

    return False


def convert_pdf(tmpfile_name, cmdname="ps2pdf"):
    new_name = "{}.pdf".format(tmpfile_name)
    try:
        subprocess.check_output([cmdname, tmpfile_name, new_name], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logger.error("Could not run {} command (returned {}): {}".format(cmdname, e.returncode, e.output))
        return False

    if os.path.isfile(new_name):
        return new_name

    return False


def get_numpages(tmpfile_name):
    try:
        output = subprocess.check_output(["pdfinfo", tmpfile_name], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logger.error("Could not run pdfinfo command (returned {}): {}".format(e.returncode, e.output))
        return -1

    lines = output.splitlines()
    num_pages = -1
    for l in lines:
        if l.startswith("Pages:"):
            try:
                num_pages = l.split("Pages:", 2)[1].strip()
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
    """Returns the number of pages in the range, or False if it is an invalid range."""
    pages = 0
    try:
        for r in page_range.split(","):  # check all ranges separated by commas
            if "-" in r:
                rr = r.split("-")
                if len(rr) != 2:  # make sure 2 values in range
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
        raise Exception("Printer not authorized.")

    if not obj.file:
        raise Exception("No file.")

    fileobj = obj.file

    filebase = os.path.basename(fileobj.name)
    filebase_escaped = slugify(filebase)
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
    if num_pages < 0:
        raise Exception("Could not get number of pages in %s" % filebase)
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

    if do_print:
        args = ["lpr", "-P", "{}".format(printer), "{}".format(tmpfile_name)]
        if obj.page_range:
            args.extend(["-o", "page-ranges={}".format(obj.page_range)])
        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            if "is not accepting jobs" in e.output:
                raise Exception(e.output.strip())
            logger.error("Could not run lpr (returned {}): {}".format(e.returncode, e.output.strip()))
            raise Exception("An error occured while printing your file: %s" % e.output.strip())

    obj.printed = True
    obj.save()


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
                logging.critical("Printing failed: %s", e)
            else:
                messages.success(request, "Your file was printed!")
    else:
        form = PrintJobForm(printers=printers)
    context = {"form": form}
    return render(request, "printing/print.html", context)
