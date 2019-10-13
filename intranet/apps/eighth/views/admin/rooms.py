import csv
import json
import logging
from collections import defaultdict

from formtools.wizard.views import SessionWizardView

from django import http
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from ....auth.decorators import eighth_admin_required
from ...forms.admin.blocks import BlockSelectionForm
from ...forms.admin.rooms import RoomForm
from ...models import EighthBlock, EighthRoom, EighthScheduledActivity
from ...utils import get_start_date

logger = logging.getLogger(__name__)


@eighth_admin_required
def add_room_view(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added room.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding room.")
            request.session["add_room_form"] = json.dumps(form.errors)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_room_view(request, room_id):
    try:
        room = EighthRoom.objects.get(id=room_id)
    except EighthRoom.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited room.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding room.")
    else:
        form = RoomForm(instance=room)

    context = {"form": form, "delete_url": reverse("eighth_admin_delete_room", args=[room_id]), "admin_page_title": "Edit Room"}
    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def delete_room_view(request, room_id):
    try:
        room = EighthRoom.objects.get(id=room_id)
    except EighthRoom.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        room.delete()
        messages.success(request, "Successfully deleted room.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Room",
            "item_name": str(room),
            "help_text": "Deleting this room will remove all records " "of it related to eighth period.",
        }

        return render(request, "eighth/admin/delete_form.html", context)


@eighth_admin_required
def room_sanity_check_view(request):
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
        room_conflicts = []
        rooms = defaultdict(list)

        sched_acts = block.eighthscheduledactivity_set.exclude(cancelled=True)
        for sched_act in sched_acts:
            for room in sched_act.get_true_rooms():
                activity = sched_act.activity
                if not activity.deleted:
                    rooms[room.name].append(activity)

        for room_name, activities in rooms.items():
            if len(activities) > 1:
                room_conflicts.append({"room_name": room_name, "activities": activities})
        context["room_conflicts"] = room_conflicts

    context["admin_page_title"] = "Room Assignment Sanity Check"
    return render(request, "eighth/admin/room_sanity_check.html", context)


@eighth_admin_required
def room_utilization_for_block_view(request):
    blocks = EighthBlock.objects.all()
    block_id = request.GET.get("block", None)

    if block_id:
        return redirect("eighth_admin_room_utilization", block_id, block_id)
    else:
        blocks = blocks.filter(date__gte=get_start_date(request))
        context = {"admin_page_title": "Room Utilization", "blocks": blocks}
        return render(request, "eighth/admin/room_utilization_for_block.html", context)


class EighthAdminRoomUtilizationWizard(SessionWizardView):
    FORMS = [("start_block", BlockSelectionForm), ("end_block", BlockSelectionForm)]

    TEMPLATES = {"start_block": "eighth/admin/room_utilization.html", "end_block": "eighth/admin/room_utilization.html"}

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = {}
        if step == "start_block":
            kwargs.update({"exclude_before_date": get_start_date(self.request)})
        if step == "end_block":
            block = self.get_cleaned_data_for_step("start_block")["block"]
            kwargs.update({"exclude_before_date": block.date})

        labels = {"start_block": "Select a start block", "end_block": "Select an end block"}

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminRoomUtilizationWizard, self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Room Utilization"})
        this_yr = EighthBlock.objects.get_blocks_this_year()
        context.update({"first_block": this_yr.first().id, "last_block": this_yr.last().id, "all_rooms": EighthRoom.objects.all()})
        return context

    def done(self, form_list, **kwargs):  # pylint: disable=unused-argument
        form_list = list(form_list)
        start_block = form_list[0].cleaned_data["block"]
        end_block = form_list[1].cleaned_data["block"]
        return redirect("eighth_admin_room_utilization", start_block.id, end_block.id)


@eighth_admin_required
def room_utilization_action(request, start_id, end_id):
    try:
        start_block = EighthBlock.objects.get(id=start_id)
        end_block = EighthBlock.objects.get(id=end_id)

        one_block = start_id == end_id
    except EighthBlock.DoesNotExist:
        raise http.Http404

    show_used_rooms = "show_used" in request.GET
    show_available_for_eighth = "show_available_for_eighth" in request.GET
    show_all_rooms = "show_all" in request.GET
    show_listing = show_all_rooms or show_used_rooms or show_available_for_eighth or ("room" in request.GET)

    if show_available_for_eighth:
        all_rooms = EighthRoom.objects.filter(available_for_eighth=True).order_by("name")
    else:
        all_rooms = EighthRoom.objects.all().order_by("name")

    # If a "show" GET parameter is defined, only show the values that are given.
    show_vals = request.GET.getlist("show")
    show_opts = ["block", "rooms", "capacity", "signups", "aid", "activity", "comments", "sponsors", "admin_comments"]
    show_opts_defaults = ["block", "rooms", "capacity", "signups", "aid", "activity", "comments", "sponsors"]
    show_opts_hidden = ["admin_comments"]
    if not show_vals:
        show = {name: True for name in show_opts_defaults}
        show.update({name: False for name in show_opts_hidden})
    else:
        show = {name: name in show_vals for name in show_opts}

    hide_administrative = "hide_administrative" in request.GET and request.GET.get("hide_administrative") != "0"
    only_show_overbooked = "only_show_overbooked" in request.GET and request.GET.get("only_show_overbooked") != "0"

    context = {
        "admin_page_title": "Room Utilization",
        "start_block": start_block,
        "end_block": end_block,
        "all_rooms": all_rooms,
        "show": show,
        "hide_administrative": hide_administrative,
        "only_show_overbooked": only_show_overbooked,
        "show_listing": show_listing,
        "show_used_rooms": show_used_rooms,
        "show_all_rooms": show_all_rooms,
        "show_available_for_eighth": show_available_for_eighth,
    }
    get_csv = request.resolver_match.url_name == "eighth_admin_room_utilization_csv"
    if show_listing or get_csv:
        sched_acts = EighthScheduledActivity.objects.exclude(activity__deleted=True)
        # .exclude(cancelled=True) # include cancelled activities
        if not one_block:
            sched_acts = sched_acts.filter(block__date__gte=start_block.date, block__date__lte=end_block.date)
        else:
            sched_acts = sched_acts.filter(block=start_block)

        room_ids = request.GET.getlist("room")
        if "room" in request.GET:
            rooms = EighthRoom.objects.filter(id__in=room_ids)
            sched_acts = sched_acts.filter(Q(rooms__in=rooms) | Q(activity__rooms__in=rooms)).distinct()

        sched_acts = sched_acts.order_by("block__date", "block__block_letter")

        if "room" in request.GET:
            all_sched_acts = sched_acts
            sched_acts = []
            for sched_act in all_sched_acts:
                if set(rooms).intersection(set(sched_act.get_true_rooms())):
                    sched_acts.append(sched_act)
        else:
            rooms = all_rooms

        sched_acts = sorted(sched_acts, key=lambda x: ("{}".format(x.block), "{}".format(x.get_true_rooms())))

        if show_all_rooms or show_available_for_eighth:
            unused = rooms.exclude(Q(eighthscheduledactivity__in=sched_acts) | Q(eighthactivity__eighthscheduledactivity__in=sched_acts))
            for room in unused:
                sched_acts.append({"room": room, "empty": True})

        context.update({"scheduled_activities": sched_acts, "rooms": rooms, "room_ids": [int(i) for i in room_ids]})

    if get_csv:
        response = http.HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="room_utilization.csv"'

        writer = csv.writer(response)

        title_row = []
        for opt in show_opts:
            if show[opt]:
                title_row.append(opt.capitalize().replace("_", " "))
        writer.writerow(title_row)

        for sch_act in sched_acts:
            row = []
            if sch_act.activity.administrative and hide_administrative:
                continue

            if not sch_act.is_overbooked() and only_show_overbooked:
                continue

            if show["block"]:
                row.append(sch_act.block)
            if show["rooms"]:
                row.append(";".join([rm.name for rm in sch_act.get_true_rooms()]))
            if show["capacity"]:
                row.append(sch_act.get_true_capacity())
            if show["signups"]:
                row.append(sch_act.members.count())
            if show["aid"]:
                row.append(sch_act.activity.aid)
            if show["activity"]:
                row.append(sch_act.activity)
            if show["comments"]:
                row.append(sch_act.comments)
            if show["sponsors"]:
                row.append(";".join([str(sp) for sp in sch_act.get_true_sponsors()]))
            if show["admin_comments"]:
                row.append(sch_act.admin_comments)

            writer.writerow(row)

        return response

    return render(request, "eighth/admin/room_utilization.html", context)


room_utilization_view = eighth_admin_required(EighthAdminRoomUtilizationWizard.as_view(EighthAdminRoomUtilizationWizard.FORMS))
