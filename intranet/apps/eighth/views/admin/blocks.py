# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
    if "date" in request.POST:
        date = request.POST.get("date")
        show_letters = True
    else:
        date = None
        show_letters = False

    letters = []
    onday = EighthBlock.objects.filter(date=date)
    for l in "ABCDEFGH":
        exists = onday.filter(block_letter=l)
        letters.append({
            "letter": l,
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
