# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import logging
from six.moves import cPickle as pickle
from django import http
from django.http import HttpResponse
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.blocks import QuickBlockForm, BlockForm
from ...models import EighthBlock, EighthScheduledActivity
from ..attendance import generate_roster_pdf
from ...serializers import EighthBlockDetailSerializer

logger = logging.getLogger(__name__)

@eighth_admin_required
def add_block_view(request):
    if request.method == "POST":
        form = QuickBlockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added block.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding block.")
            request.session["add_block_form"] = pickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "405: METHOD NOT ALLOWED")

@eighth_admin_required
def add_multiple_blocks_view(request):
    date = None
    show_letters = None

    if "date" in request.GET:
        date = request.GET.get("date")
    if "date" in request.POST:
        date = request.POST.get("date")
    if date:
        date_format = re.compile(r'([0-9]{2})\/([0-9]{2})\/([0-9]{4})')
        fmtdate = date_format.sub(r'\3-\1-\2', date)
        logger.debug(fmtdate)
        show_letters = True

        if "modify_blocks" in request.POST:
            letters = request.POST.getlist("blocks")
            current_letters = []
            blocks_day = EighthBlock.objects.filter(date=fmtdate)
            for day in blocks_day:
                current_letters.append(day.block_letter)
            logger.debug(letters)
            logger.debug(current_letters)
            for l in letters:
                if l not in current_letters:
                    EighthBlock.objects.create(date=fmtdate, block_letter=l)
                    messages.success(request, "Successfully added {} Block on {}".format(l, fmtdate))
            for l in current_letters:
                if l not in letters:
                    EighthBlock.objects.get(date=fmtdate, block_letter=l).delete()
                    messages.success(request, "Successfully removed {} Block on {}".format(l, fmtdate))



    letters = []
    if show_letters:
        onday = EighthBlock.objects.filter(date=fmtdate)
        for l in "ABCDEFGH":
            exists = onday.filter(block_letter=l)
            letters.append({
                "name": l,
                "exists": exists
            })


    context = {
        "date": date,
        "letters": letters,
        "show_letters": show_letters
    }

    return render(request, "eighth/admin/add_multiple_blocks.html", context)


@eighth_admin_required
def edit_block_view(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        form = BlockForm(request.POST, instance=block)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited block.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding block.")
    else:
        form = BlockForm(instance=block)

    context = {
        "form": form,
        "delete_url": reverse("eighth_admin_delete_block",
                              args=[block_id]),
        "admin_page_title": "Edit Block"
    }
    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def delete_block_view(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        block.delete()
        messages.success(request, "Successfully deleted block.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Block",
            "item_name": str(block),
            "help_text": "Deleting this block will remove all records "
                         "of it related to eighth period."
        }

        return render(request, "eighth/admin/delete_form.html", context)


@eighth_admin_required
def print_block_rosters_view(request, block_id):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=\"block_{}_rosters.pdf\"".format(block_id)
    sched_act_ids = (EighthScheduledActivity.objects
                                            .filter(block=block_id)
                                            .values_list("id", flat=True))

    pdf_buffer = generate_roster_pdf(sched_act_ids, True)
    response.write(pdf_buffer.getvalue())
    pdf_buffer.close()
    return response
