# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.sponsors import SponsorForm
from ...models import EighthSponsor, EighthScheduledActivity


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
def edit_sponsor_view(request, sponsor_id):
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
        "admin_page_title": "Edit Sponsor",
        "delete_url": reverse("eighth_admin_delete_sponsor",
                              args=[sponsor_id])
    }
    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def delete_sponsor_view(request, sponsor_id):
    try:
        sponsor = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        return http.HttpResponseNotFound()

    if request.method == "POST":
        sponsor.delete()
        messages.success(request, "Successfully deleted sponsor.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Sponsor",
            "help_text": "Deleting this sponsor will remove all records "
                         "of this user related to eighth period, but will "
                         "not remove the actual associated user if "
                         "there is one."
        }

        return render(request, "eighth/admin/delete_form.html", context)


@eighth_admin_required
def sponsor_schedule_view(request, sponsor_id):
    try:
        sponsor = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        return http.HttpResponseNotFound()

    sponsoring_filter = (Q(sponsors=sponsor) |
                         (Q(sponsors=None) & Q(activity__sponsors=sponsor)))
    sched_acts = EighthScheduledActivity.objects \
                                        .exclude(activity__deleted=True) \
                                        .exclude(cancelled=True) \
                                        .filter(sponsoring_filter) \
                                        .order_by("block__date",
                                                  "block__block_letter")

    context = {
        "scheduled_activities": sched_acts,
        "admin_page_title": "Sponsor Schedule",
        "sponsor": sponsor
    }

    return render(request, "eighth/admin/sponsor_schedule.html", context)
