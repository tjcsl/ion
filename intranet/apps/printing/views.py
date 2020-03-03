import logging
import math
import os
import re
import subprocess
import tempfile
from typing import Dict, Optional

import magic
from sentry_sdk import add_breadcrumb, capture_exception

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.text import slugify

from ..auth.decorators import deny_restricted
from ..context_processors import _get_current_ip
from .forms import PrintJobForm
from .models import PrintJob

logger = logging.getLogger(__name__)


class InvalidInputPrintingError(Exception):
    """An error occurred while printing, but it was due to invalid input from the user and is not worthy of a ``CRITICAL`` log message."""


def get_printers() -> Dict[str, str]:
    """Returns a dictionary mapping name:description for available printers.

    This requires that a CUPS client be configured on the server.
    Otherwise, this returns an empty dictionary.

    Returns:
        A dictionary mapping name:description for available printers.
    """

    key = "printing:printers"
    cached = cache.get(key)
    if cached and isinstance(cached, dict):
        return cached
    else:
        try:
            output = subprocess.check_output(["lpstat", "-l", "-p"], universal_newlines=True, timeout=10)
        # Don't die if cups isn't installed.
        except FileNotFoundError:
            return []
        # Don't die if lpstat fails
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []

        PRINTER_LINE_RE = re.compile(r"^printer\s+(\w+)", re.ASCII)
        DESCRIPTION_LINE_RE = re.compile(r"^\s+Description:\s+(.*)\s*$", re.ASCII)

        printers = {}
        last_name = None
        for line in output.splitlines():
            match = PRINTER_LINE_RE.match(line)
            if match is not None:
                # Pull out the name of the printer
                name = match.group(1)
                if name != "Please_Select_a_Printer":
                    # By default, use the name of the printer instead of the description
                    printers[name] = name
                    # Record the name of the printer so when we parse the rest of the
                    # extended description we know which printer it's referring to.
                    last_name = name
            else:
                # If we've seen a line with the name of a printer before
                if last_name is not None:
                    match = DESCRIPTION_LINE_RE.match(line)
                    if match is not None:
                        # Pull out the description
                        description = match.group(1)
                        # And make sure we don't set an empty description
                        if description:
                            printers[last_name] = description

        cache.set(key, printers, timeout=settings.CACHE_AGE["printers_list"])
        return printers


def convert_soffice(tmpfile_name: str) -> Optional[str]:
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
        return None

    if " -> " in output and " using " in output:  # pylint: disable=unsupported-membership-test; Pylint is wrong
        fileout = output.split(" -> ", 2)[1]
        fileout = fileout.split(" using ", 1)[0]
        return fileout

    logger.error("soffice command succeeded, but we couldn't find the file name in the output: %r", output)

    return None


def convert_pdf(tmpfile_name: str, cmdname: str = "ps2pdf") -> Optional[str]:
    new_name = "{}.pdf".format(tmpfile_name)
    try:
        output = subprocess.check_output([cmdname, tmpfile_name, new_name], stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logger.error("Could not run %s command (returned %d): %s", cmdname, e.returncode, e.output)
        return None

    if os.path.isfile(new_name):
        return new_name

    logger.error("%s command succeeded, but the file it was supposed to create (%s) does not exist: %r", cmdname, new_name, output)

    return None


def get_numpages(tmpfile_name: str) -> int:
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


def get_mimetype(tmpfile_name: str) -> str:
    mime = magic.Magic(mime=True)
    mimetype = mime.from_file(tmpfile_name)

    if mimetype in EXTRA_MAGIC_FILES:
        magic_files = ":".join(os.path.join(os.path.dirname(__file__), "magic_files", fname) for fname in EXTRA_MAGIC_FILES[mimetype])

        mime = magic.Magic(mime=True, magic_file=magic_files)
        new_mimetype = mime.from_file(tmpfile_name)
        if new_mimetype not in GENERIC_MIMETYPES:
            mimetype = new_mimetype

    return mimetype


def convert_file(tmpfile_name: str, orig_fname: str) -> Optional[str]:
    detected = get_mimetype(tmpfile_name)

    add_breadcrumb(category="printing", message="Detected file type {}".format(detected), level="debug")

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


def check_page_range(page_range: str, max_pages: int) -> Optional[int]:
    """Returns the number of pages included in the range, or None if it is an invalid range.

    Args:
        page_range: The page range as a string, such as "1-5" or "1,2,3".
        max_pages: The number of pages in the submitted document. If the number of pages in the
            given range exceeds this, it will be considered invalid.

    Returns:
        The number of pages in the range, or None if it is an invalid range.

    """
    pages = 0
    try:
        for single_range in page_range.split(","):  # check all ranges separated by commas
            if "-" in single_range:
                if single_range.count("-") > 1:
                    return None

                range_low, range_high = map(int, single_range.split("-"))

                # check in page range
                if range_low <= 0 or range_high <= 0 or range_low > max_pages or range_high > max_pages:
                    return None

                if range_low > range_high:  # check lower bound <= upper bound
                    return None

                pages += range_high - range_low + 1
            else:
                single_range = int(single_range)
                if single_range <= 0 or single_range > max_pages:  # check in page range
                    return None

                pages += 1
    except ValueError:  # catch int parse fail
        return None
    return pages


def print_job(obj: PrintJob, do_print: bool = True):
    printer = obj.printer
    if printer not in get_printers().keys():
        raise Exception("Printer not authorized.")

    if not obj.file:
        raise InvalidInputPrintingError("No file given to print.")

    fileobj = obj.file

    filebase = os.path.basename(fileobj.name)
    filebase_escaped = slugify(filebase)

    # The paths to files that we need to clean up at the end
    # This needs to be a set because we may add duplicate entries to it
    delete_filenames = set()
    try:
        tmpfile_fd, tmpfile_name = tempfile.mkstemp(prefix="ion_print_{}_{}".format(obj.user.username, filebase_escaped), text=False)
        delete_filenames.add(tmpfile_name)

        # This implicitly closes tmpfile_fd when it's done writing
        with open(tmpfile_fd, "wb") as dest:
            for chunk in fileobj.chunks():
                dest.write(chunk)

        final_filename = convert_file(tmpfile_name, filebase)
        if final_filename is not None:
            delete_filenames.add(final_filename)

        if not final_filename:
            msg = "Error converting file to PDF for printing"

            if filebase.endswith((".doc", ".docx")):
                msg += (
                    "<br>Note: It looks like you are trying to print a Word document. Word documents don't always print correctly, so we recommend "
                    "that you convert to a PDF before printing."
                )

            raise Exception(msg)

        if get_mimetype(final_filename) == "text/plain":
            # These numbers were obtained by printing a text file with 1) repetitive sequences of characters
            # to see how many characters can fit on a line and 2) line numbers to see how many lines can fit
            # on a page.
            line_width = 81
            lines_per_page = 62

            with open(final_filename, "r") as f:
                # Every newline-terminated line of the file will take up 1 printed line, plus an
                # additional printed line for each time it wraps.
                # We subtract 1 from the line length because having exactly `line_width` characters
                # won't make it wrap; we need one more character to actually wrap. (More generally,
                # to make n additional printed lines wrap you need at least `line_width * n + 1`
                # characters).
                # However, subtracting one also means we need to clamp it so it won't go below zero.
                num_lines = sum(1 + (max(0, len(line.rstrip("\n")) - 1) // line_width) for line in f)

            num_pages = math.ceil(num_lines / lines_per_page)
        else:
            num_pages = get_numpages(final_filename)
            if num_pages < 0:
                raise Exception("Could not get number of pages in {}".format(filebase))

        if re.search(r"\d\s+\d", obj.page_range) is not None:
            # Make sure that when removing spaces in the page range we don't accidentally combine two numbers
            raise InvalidInputPrintingError(
                "You specified an invalid page range (please separate page numbers with 1) commas to print selected pages or 2) dashes to print a "
                "range)."
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
            args = ["lpr", "-P", printer, final_filename]

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
    finally:
        for filename in delete_filenames:
            os.remove(filename)


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
                logging.error("Printing failed: %s", e)
                capture_exception(e)
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
