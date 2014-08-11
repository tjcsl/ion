# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.forms.formsets import formset_factory
from django.shortcuts import render, redirect
from ....auth.decorators import eighth_admin_required
from ...models import EighthBlock, EighthActivity, EighthScheduledActivity
from ...forms.admin.blocks import BlockSelectionForm
from ...forms.admin.activities import ActivitySelectionForm
from ...forms.admin.scheduling import ScheduledActivityForm
from ...utils import get_start_date

logger = logging.getLogger(__name__)


@eighth_admin_required
def schedule_activity_view(request):
    ScheduledActivityFormset = formset_factory(ScheduledActivityForm, extra=0)

    if request.method == "POST":
        formset = ScheduledActivityFormset(request.POST)

        if formset.is_valid():
            for form in formset:
                block = form.cleaned_data["block"]
                activity = form.cleaned_data["activity"]

                if form["scheduled"].value():
                    instance, created = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)

                    # TODO: Send notifications about room changes

                    fields = ["rooms", "capacity", "sponsors", "comments"]
                    for field_name in fields:
                        setattr(instance, field_name, form.cleaned_data[field_name])

                    # Uncancel if this activity/block pairing was already
                    # created and cancelled
                    instance.cancelled = False
                    instance.save()
                else:
                    # Instead of deleting and messing up attendance,
                    # cancel the scheduled activity if it was unscheduled
                    EighthScheduledActivity.objects.filter(block=block, activity=activity).update(cancelled=True)

            messages.success(request, "Successfully updated schedule.")

            # Force reload everything from the database to reset
            # forms that weren't saved
            return redirect(request.get_full_path())
        else:
            messages.error(request, "Error updating schedule.")

    activities = EighthActivity.undeleted_objects.order_by("name")
    activity_id = request.GET.get("activity", None)
    activity = None

    if activity_id is not None:
        try:
            activity = EighthActivity.undeleted_objects.get(id=activity_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {
        "activities": activities,
        "activity": activity
    }

    if activity is not None:
        start_date = get_start_date(request)
        blocks = EighthBlock.objects.filter(date__gte=start_date) \
                                    .order_by("date")

        initial_formset_data = []

        for block in blocks:
            initial_form_data = {
                "block": block,
                "activity": activity
            }
            try:
                sched_act = EighthScheduledActivity.objects \
                                                   .exclude(cancelled=True) \
                                                   .get(activity=activity,
                                                        block=block)

                initial_form_data.update({
                    "rooms": sched_act.rooms.all(),
                    "capacity": sched_act.capacity,
                    "sponsors": sched_act.sponsors.all(),
                    "comments": sched_act.comments,
                    "scheduled": True
                })
            except EighthScheduledActivity.DoesNotExist:
                pass

            initial_formset_data.append(initial_form_data)

        if request.method != "POST":
            # There must be an error in the form if this is reached
            formset = ScheduledActivityFormset(initial=initial_formset_data)
        context["formset"] = formset
        context["rows"] = zip(blocks, formset)

        context["default_rooms"] = ", ".join(map(str, activity.rooms.all()))
        context["default_sponsors"] = ", ".join(map(str, activity.sponsors.all()))
        context["default_capacity"] = activity.capacity

    return render(request, "eighth/admin/schedule_activity.html", context)


@eighth_admin_required
def show_activity_schedule_view(request):
    activities = EighthActivity.undeleted_objects.order_by("name")
    activity_id = request.GET.get("activity", None)
    activity = None

    if activity_id is not None:
        try:
            activity = EighthActivity.undeleted_objects.get(id=activity_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {
        "activities": activities,
        "activity": activity
    }

    if activity is not None:
        start_date = get_start_date(request)
        scheduled_activities = activity.eighthscheduledactivity_set \
                                       .filter(block__date__gte=start_date) \
                                       .order_by("block__date",
                                                 "block__block_letter")
        context["scheduled_activities"] = scheduled_activities

    return render(request, "eighth/admin/view_activity_schedule.html", context)


class EighthAdminTransferStudentsWizard(SessionWizardView):
    FORMS = [
        ("block_1", BlockSelectionForm),
        ("activity_1", ActivitySelectionForm),
        ("block_2", BlockSelectionForm),
        ("activity_2", ActivitySelectionForm)
    ]

    TEMPLATES = {
        "block_1": "eighth/admin/transfer_students.html",
        "activity_1": "eighth/admin/transfer_students.html",
        "block_2": "eighth/admin/transfer_students.html",
        "activity_2": "eighth/admin/transfer_students.html"
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "activity_1":
            block = self.get_cleaned_data_for_step("block_1")["block"]
            kwargs.update({"block": block})
        if step == "activity_2":
            block = self.get_cleaned_data_for_step("block_2")["block"]
            kwargs.update({"block": block})

        labels = {
            "block_1": "Select a block to move students from",
            "activity_1": "Select an activity to move students from",
            "block_2": "Select a block to move students to",
            "activity_2": "Select an activity to move students to",
        }

        kwargs.update({"label": labels[step]})

        return kwargs

    def done(self, form_list, **kwargs):
        source_block = form_list[0].cleaned_data["block"]
        source_activity = form_list[1].cleaned_data["activity"]
        source_scheduled_activity = EighthScheduledActivity.objects.get(block=source_block, activity=source_activity)

        dest_block = form_list[2].cleaned_data["block"]
        dest_activity = form_list[3].cleaned_data["activity"]
        dest_scheduled_activity = EighthScheduledActivity.objects.get(block=dest_block, activity=dest_activity)

        source_scheduled_activity.eighthsignup_set.update(scheduled_activity=dest_scheduled_activity)

        messages.success(self.request, "Successfully transfered students.")
        return redirect("eighth_admin_dashboard")
