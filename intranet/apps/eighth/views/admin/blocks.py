# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves import cPickle as pickle
from django import http
from django.contrib import messages
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.blocks import QuickBlockForm, BlockForm
from ...models import EighthBlock


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
def edit_block_view(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        return http.HttpResponseNotFound()

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
        "admin_page_title": "Edit Block"
    }
    return render(request, "eighth/admin/edit_form.html", context)
