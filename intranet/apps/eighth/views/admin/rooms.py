# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
import cPickle
from django import http
from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.blocks import BlockSelectionForm
from ...forms.admin.rooms import RoomForm
from ...models import EighthRoom, EighthBlock, EighthScheduledActivity


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
            request.session["add_room_form"] = cPickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_room_view(request, room_id):
    try:
        room = EighthRoom.objects.get(id=room_id)
    except EighthRoom.DoesNotExist:
        return http.HttpResponseNotFound()

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

    context = {
        "form": form,
        "admin_page_title": "Edit Room"
    }
    return render(request, "eighth/admin/edit_form.html", context)


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

    context = {
        "blocks": blocks,
        "chosen_block": block
    }

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
                room_conflicts.append({
                    "room_name": room_name,
                    "activities": activities
                })
        context["room_conflicts"] = room_conflicts

    context["admin_page_title"] = "Room Assignment Sanity Check"
    return render(request, "eighth/admin/room_sanity_check.html", context)


@eighth_admin_required
def room_utilization_for_block_view(request):
    blocks = EighthBlock.objects.all()
    block_id = request.GET.get("block", None)
    block = None

    if block_id is not None:
        try:
            block = EighthBlock.objects.get(id=block_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {
        "blocks": blocks,
        "chosen_block": block
    }

    if block is not None:
        scheduled_activities = (EighthScheduledActivity.objects
                                                       .exclude(activity__deleted=True)
                                                       .exclude(cancelled=True)
                                                       .filter(block=block))
        context["scheduled_activities"] = scheduled_activities

    context["admin_page_title"] = "Room Utilization for Block"
    return render(request, "eighth/admin/room_utilization_for_block.html", context)


class EighthAdminRoomUtilizationWizard(SessionWizardView):
    FORMS = [
        ("start_block", BlockSelectionForm),
        ("end_block", BlockSelectionForm),
    ]

    TEMPLATES = {
        "start_block": "eighth/admin/room_utilization.html",
        "end_block": "eighth/admin/room_utilization.html",
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "end_block":
            block = self.get_cleaned_data_for_step("start_block")["block"]
            kwargs.update({"exclude_before_date": block.date})

        labels = {
            "start_block": "Select a start block",
            "end_block": "Select an end block",
        }

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminRoomUtilizationWizard,
                        self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Room Utilization"})
        return context

    def done(self, form_list, **kwargs):
        start_block = form_list[0].cleaned_data["block"]
        end_block = form_list[1].cleaned_data["block"]
        sched_acts = (EighthScheduledActivity.objects
                                             .exclude(activity__deleted=True)
                                             .exclude(cancelled=True)
                                             .filter(block__date__gte=start_block.date,
                                                     block__date__lte=end_block.date)
                                             .order_by("block__date",
                                                       "block__block_letter"))

        context = {
            "scheduled_activities": sched_acts,
            "admin_page_title": "Room Utilization",
            "start_block": start_block,
            "end_block": end_block
        }

        return render(self.request, "eighth/admin/room_utilization.html", context)

room_utilization_view = eighth_admin_required(
    EighthAdminRoomUtilizationWizard.as_view(
        EighthAdminRoomUtilizationWizard.FORMS
    )
)
