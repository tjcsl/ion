import logging
import os
import re
import subprocess
import tempfile

import magic

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.text import slugify

from ..auth.decorators import deny_restricted
from ..context_processors import _get_current_ip
from .forms import PrintJobForm

logger = logging.getLogger(__name__)


class InvalidInputPrintingError(Exception):
    """An error occurred while printing, but it was due to invalid input from the user and is not worthy of a ``CRITICAL`` log message."""


def get_printers():
    """ Returns the list of available printers.

    This requires that a CUPS client be configured on the server.
    Otherwise, this returns an empty list.

    Returns:
        A list of available printers.
    """

    key = "printing:printers"
    cached = cache.get(key)
    if cached:
        return cached
    else:
        try:
            output = subprocess.check_output(["lpstat", "-a"], universal_newlines=True, timeout=10)
        # Don't die if cups isn't installed.
        except FileNotFoundError:
            return []
        # Don't die if lpstat -a fails
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []
        lines = output.splitlines()
        names = []
        for line in lines:
            if "requests since" in line:
                names.append(line.split(" ", 1)[0])

        if "Please_Select_a_Printer" in names:
            names.remove("Please_Select_a_Printer")

        if "" in names:
            names.remove("")

        cache.set(key, names, timeout=settings.CACHE_AGE["printers_list"])
        return names


def convert_soffice(tmpfile_name):
    """ Converts a doc or docx to a PDF with soffice.

    Args:
        tmpfile_name: The path to the file to print.

    Returns:
        The path to the converted file. If it fails, false.
    """

    try:
        output = subprocess.check_output(
            ["soffice", "--headless", "--convert-to", "pdf", tmpfile_name, "--outdir", "/tmp"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as e:
        logger.error("Could not run soffice command (returned %d): %s", e.returncode, e.output)
        return False

    if " -> " in output and " using " in output:  # pylint: disable=unsupported-membership-test; Pylint is wrong
        fileout = output.split(" -> ", 2)[1]
        fileout = fileout.split(" using ", 1)[0]
        return fileout

    return False


def convert_pdf(tmpfile_name, cmdname="ps2pdf"):
    new_name = "{}.pdf".format(tmpfile_name)
    try:
        subprocess.check_output([cmdname, tmpfile_name, new_name], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logger.error("Could not run %s command (returned %d): %s", cmdname, e.returncode, e.output)
        return False

    if os.path.isfile(new_name):
        return new_name

    return False


def get_numpages(tmpfile_name):
    try:
        output = subprocess.check_output(["pdfinfo", tmpfile_name], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logger.error("Could not run pdfinfo command (returned %d): %s", e.returncode, e.output)
        return -1

    lines = output.splitlines()
    num_pages = -1
    pages_prefix = "Pages:"
    for line in lines:
        if line.startswith(pages_prefix):
            try:
                num_pages = int(line[len(pages_prefix):].strip())
            except ValueError:
                num_pages = -1

    return num_pages


# If a file is identified as a mimetype that is a key in this dictionary, the magic files (in the "magic_files" director) from the corresponding list
# will be used to re-examine the file and attempt to find a better match.
# Why not just always use those files? Well, if you give libmagic a list of files, it will check *only* the files you tell it to, excluding the
# system-wide magic database. Worse, there is no reliable method of getting the system-wide database path (which is distro-specific, so we can't just
# hardcode it). This really is the best solution.
EXTRA_MAGIC_FILES = {"application/zip": ["msooxml"]}
# If the re-examination of a file with EXTRA_MAGIC_FILES yields one of these mimetypes, the original mimetype (the one that prompted re-examining
# based on EXTRA_MAGIC_FILES) will be used instead.
GENERIC_MIMETYPES = {"application/octet-stream"}


def get_mimetype(tmpfile_name):
    mime = magic.Magic(mime=True)
    mimetype = mime.from_file(tmpfile_name)

    if mimetype in EXTRA_MAGIC_FILES:
        magic_files = ":".join(os.path.join(os.path.dirname(__file__), "magic_files", fname) for fname in EXTRA_MAGIC_FILES[mimetype])

        mime = magic.Magic(mime=True, magic_file=magic_files)
        new_mimetype = mime.from_file(tmpfile_name)
        if new_mimetype not in GENERIC_MIMETYPES:
            mimetype = new_mimetype

    return mimetype


def convert_file(tmpfile_name, orig_fname):
    detected = get_mimetype(tmpfile_name)
    no_conversion = ["application/pdf", "text/plain"]
    soffice_convert = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/vnd.oasis.opendocument.text",
    ]
    if detected in no_conversion:
        return tmpfile_name

    # .docx
    if detected in soffice_convert:
        return convert_soffice(tmpfile_name)

    if detected == "application/postscript":
        return convert_pdf(tmpfile_name, "pdf2ps")

    # Not detected

    if orig_fname.endswith((".doc", ".docx")):
        raise InvalidInputPrintingError(
            "Invalid file type {}<br>Note: It looks like you are trying to print a Word document. Word documents don't always print correctly, so we "
            "recommend that you convert to a PDF before printing.".format(detected)
        )

    raise InvalidInputPrintingError("Invalid file type {}".format(detected))


def check_page_range(page_range, max_pages):
    """Returns the number of pages in the range, or False if it is an invalid range."""
    pages = 0
    try:
        for single_range in page_range.split(","):  # check all ranges separated by commas
            if "-" in single_range:
                if single_range.count("-") > 1:
                    return False

                range_low, range_high = map(int, single_range.split("-"))

                # check in page range
                if range_low <= 0 or range_high <= 0 or range_low > max_pages or range_high > max_pages:
                    return False

                if range_low > range_high:  # check lower bound <= upper bound
                    return False

                pages += range_high - range_low + 1
            else:
                single_range = int(single_range)
                if single_range <= 0 or single_range > max_pages:  # check in page range
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
        raise InvalidInputPrintingError("No file given to print.")

    fileobj = obj.file

    filebase = os.path.basename(fileobj.name)
    filebase_escaped = slugify(filebase)
    tmpfile_name = tempfile.NamedTemporaryFile(prefix="ion_print_{}_{}".format(obj.user.username, filebase_escaped)).name
    with open(tmpfile_name, "wb+") as dest:
        for chunk in fileobj.chunks():
            dest.write(chunk)

    logger.debug(tmpfile_name)

    tmpfile_name = convert_file(tmpfile_name, filebase)
    logger.debug(tmpfile_name)

    if not tmpfile_name:
        raise Exception("Could not convert file.")

    if get_mimetype(tmpfile_name) == "text/plain":
        with open(tmpfile_name, "r") as f:
            num_chars = sum(len(line) for line in f)
        num_pages = num_chars // (settings.PRINTING_PAGES_LIMIT * 50 * 72)
    else:
        num_pages = get_numpages(tmpfile_name)
        if num_pages < 0:
            raise Exception("Could not get number of pages in {}".format(filebase))

    if re.search(r"\d\s+\d", obj.page_range) is not None:
        # Make sure that when removing spaces in the page range we don't accidentally combine two numbers
        raise InvalidInputPrintingError(
            "You specified an invalid page range (please separate page numbers with 1) commas to print selected pages or 2) dashes to print a range)."
        )

    obj.num_pages = num_pages
    obj.page_range = "".join(obj.page_range.split())  # remove all spaces
    obj.save()

    range_count = check_page_range(obj.page_range, obj.num_pages)

    if obj.page_range:
        if not range_count:
            raise InvalidInputPrintingError("You specified an invalid page range.")
        elif range_count > settings.PRINTING_PAGES_LIMIT:
            raise InvalidInputPrintingError(
                "You specified a range of {} pages. You may only print up to {} pages using this tool.".format(
                    range_count, settings.PRINTING_PAGES_LIMIT
                )
            )
    elif num_pages > settings.PRINTING_PAGES_LIMIT:
        raise InvalidInputPrintingError(
            "This file contains {} pages. You may only print up to {} pages using this tool.".format(num_pages, settings.PRINTING_PAGES_LIMIT)
        )

    if do_print:
        args = ["lpr", "-P", "{}".format(printer), "{}".format(tmpfile_name)]

        if obj.page_range:
            args.extend(["-o", "page-ranges={}".format(obj.page_range)])

        if obj.duplex:
            args.extend(["-o", "sides=two-sided-long-edge"])
        else:
            args.extend(["-o", "sides=one-sided"])

        if obj.fit:
            args.extend(["-o", "fit-to-page"])

        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            if "is not accepting jobs" in e.output:
                raise Exception(e.output.strip())

            logger.error("Could not run lpr (returned %d): %s", e.returncode, e.output.strip())
            raise Exception("An error occured while printing your file: {}".format(e.output.strip()))

    obj.printed = True
    obj.save()


@login_required
@deny_restricted
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
            except InvalidInputPrintingError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, str(e))
                logging.critical("Printing failed: %s", e)
            else:
                messages.success(
                    request,
                    "Your file was submitted to the printer. "
                    "If the printers are experiencing trouble, please contact the "
                    "Student Systems Administrators by filling out the feedback "
                    "form.",
                )
    else:
        form = PrintJobForm(printers=printers)
    context = {"form": form}
    return render(request, "printing/print.html", context)
