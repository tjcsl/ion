import csv
import re
from collections import defaultdict

from django import http
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from ....auth.decorators import eighth_admin_required
from ...forms.admin.sponsors import SponsorForm
from ...models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSponsor
from ...utils import get_start_date


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
    else:
        form = SponsorForm()

    context = {"admin_page_title": "Add Sponsor", "form": form}
    return render(request, "eighth/admin/add_sponsor.html", context)


@eighth_admin_required
def list_sponsor_view(request):
    blocks = EighthBlock.objects.all()
    block_id = request.GET.get("block", None)
    block = None

    if block_id is not None:
        try:
            block = EighthBlock.objects.get(id=block_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass
    else:
        blocks = blocks.filter(date__gte=get_start_date(request))

    context = {"blocks": blocks, "chosen_block": block}

    if block is not None:
        acts = EighthScheduledActivity.objects.filter(block=block)
        lst = {}
        for sponsor in EighthSponsor.objects.all():
            lst[sponsor] = []
        for act in acts.prefetch_related("sponsors").prefetch_related("rooms"):
            for sponsor in act.get_true_sponsors():
                lst[sponsor].append(act)
        lst = sorted(lst.items(), key=lambda x: x[0].name)
        context["sponsor_list"] = lst

        get_csv = request.resolver_match.url_name == "eighth_admin_list_sponsor_csv"

        if get_csv:
            response = http.HttpResponse(content_type="text/csv")
            block_str = "{}{}".format(block.date.strftime("%Y%m%d"), re.sub(r"\W+", "", block.block_letter))
            response["Content-Disposition"] = 'attachment; filename="sponsor_list_{}.csv"'.format(block_str)
            writer = csv.writer(response)
            writer.writerow(["Sponsor", "Activity", "Room", "Eighth Contracted", "Signups", "Capacity"])
            for row in context["sponsor_list"]:
                writer.writerow(
                    [
                        row[0].name,
                        "\n".join([x.full_title for x in row[1]]),
                        "\n".join([", ".join([str(y) for y in x.get_true_rooms()]) for x in row[1]]),
                        row[0].contracted_eighth,
                        "\n".join([str(x.members.count()) for x in row[1]]),
                        "\n".join([str(x.get_true_capacity()) for x in row[1]]),
                    ]
                )
            return response

    context["admin_page_title"] = "Sponsor Schedule List"
    return render(request, "eighth/admin/list_sponsors.html", context)


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

    context = {"form": form, "admin_page_title": "Edit Sponsor", "delete_url": reverse("eighth_admin_delete_sponsor", args=[sponsor_id])}
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
            "there is one).",
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
    sched_acts = (
        EighthScheduledActivity.objects.for_sponsor(sponsor, True).filter(block__date__gte=start_date).order_by("block__date", "block__block_letter")
    )

    # Find list of all activities before the list is filtered to only show one activity
    activities = set()
    for sched_act in sched_acts:
        activities.add(sched_act.activity)
    activities = list(activities)

    activity = None
    if "activity" in request.GET:
        activity_id = request.GET.get("activity")
        activity = EighthActivity.objects.get(id=activity_id)
        sched_acts = sched_acts.filter(activity=activity)

    context = {
        "scheduled_activities": sched_acts,
        "activities": activities,
        "activity": activity,
        "admin_page_title": "Sponsor Schedule",
        "sponsor": sponsor,
        "all_sponsors": EighthSponsor.objects.all(),
    }

    return render(request, "eighth/admin/sponsor_schedule.html", context)


@eighth_admin_required
def sponsor_sanity_check_view(request):
    blocks = EighthBlock.objects.all()
    block_id = request.GET.get("block", None)
    block = None

    if block_id is not None:
        try:
            block = EighthBlock.objects.get(id=block_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass
    else:
        blocks = blocks.filter(date__gte=get_start_date(request))

    context = {"blocks": blocks, "chosen_block": block}

    if block is not None:
        sponsor_conflicts = []
        sponsors = defaultdict(list)

        sched_acts = block.eighthscheduledactivity_set.exclude(cancelled=True)
        for sched_act in sched_acts:
            for sponsor in sched_act.get_true_sponsors():
                activity = sched_act.activity
                if not activity.deleted:
                    sponsors[sponsor.name].append(activity)

        for sponsor_name, activities in sponsors.items():
            if len(activities) > 1:
                sponsor_conflicts.append({"sponsor_name": sponsor_name, "activities": activities})
        context["sponsor_conflicts"] = sponsor_conflicts

    context["admin_page_title"] = "Sponsor Assignment Sanity Check"
    return render(request, "eighth/admin/sponsor_sanity_check.html", context)
