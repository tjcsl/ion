# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
from django import http
from django.contrib import messages
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.sponsors import SponsorForm
from ...models import EighthSponsor


@eighth_admin_required
def add_sponsor_view(request):
    if request.method == "POST":
        form = SponsorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added sponsor.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding sponsor.")
            request.session["add_sponsor_form"] = cPickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_sponsor_view(request, sponsor_id=None):
    try:
        sponsor = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        return http.HttpResponseNotFound()

    if request.method == "POST":
        form = SponsorForm(request.POST, instance=sponsor)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited sponsor.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding sponsor.")
    else:
        form = SponsorForm(instance=sponsor)

    context = {
        "form": form,
        "admin_page_title": "Edit Sponsor"
    }
    return render(request, "eighth/admin/edit_form.html", context)
