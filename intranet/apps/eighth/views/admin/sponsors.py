# -*- coding: utf-8 -*-

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render

from six.moves import cPickle

from ...forms.admin.sponsors import SponsorForm
from ...models import EighthActivity, EighthScheduledActivity, EighthSponsor
from ...utils import get_start_date
from ....auth.decorators import eighth_admin_required


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

    context = {
        "admin_page_title": "Add Sponsor",
        "form": SponsorForm
    }
    return render(request, "eighth/admin/add_sponsor.html", context)


@eighth_admin_required
def edit_sponsor_view(request, sponsor_id):
    try:
        sponsor = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        raise http.Http404

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
        raise http.Http404

    if request.method == "POST":
        sponsor.delete()
        messages.success(request, "Successfully deleted sponsor.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Sponsor",
            "item_name": str(sponsor),
            "help_text": "Deleting this sponsor will remove all records "
                         "of this user related to eighth period, but will "
                         "not remove the user account associated with it (if "
                         "there is one)."
        }

        return render(request, "eighth/admin/delete_form.html", context)


@eighth_admin_required
def sponsor_schedule_view(request, sponsor_id):
    try:
        sponsor = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        raise http.Http404

    start_date = get_start_date(request)

    # for_sponsor() excludes cancelled activities
    sched_acts = (EighthScheduledActivity.objects.for_sponsor(sponsor, True)
                                         .filter(block__date__gte=start_date)
                                         .order_by("block__date",
                                                   "block__block_letter"))

    # Find list of all activities before the list is filtered to only show one activity
    activities = set()
    for sched_act in sched_acts:
        activities.add(sched_act.activity)
    activities = list(activities)

    activity = None
    if "activity" in request.GET:
        activity_id = request.GET.get('activity')
        activity = EighthActivity.objects.get(id=activity_id)
        sched_acts = sched_acts.filter(activity=activity)

    context = {
        "scheduled_activities": sched_acts,
        "activities": activities,
        "activity": activity,
        "admin_page_title": "Sponsor Schedule",
        "sponsor": sponsor,
        "all_sponsors": EighthSponsor.objects.all()
    }

    return render(request, "eighth/admin/sponsor_schedule.html", context)
