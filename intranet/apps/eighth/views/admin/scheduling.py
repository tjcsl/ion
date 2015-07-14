# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import timedelta
from django.contrib import messages
from django.forms.formsets import formset_factory
from django.shortcuts import render, redirect
from formtools.wizard.views import SessionWizardView
from .....utils.serialization import safe_json
from ....auth.decorators import eighth_admin_required
from ...models import (
    EighthBlock, EighthActivity, EighthScheduledActivity, EighthSponsor,
    EighthRoom
)
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

                # Save changes to cancelled activities and scheduled activities
                cancelled = (EighthScheduledActivity.objects
                                                    .filter(block=block,
                                                            activity=activity,
                                                            cancelled=True)
                                                    .exists())

                if form["scheduled"].value() or cancelled:
                    instance, created = (EighthScheduledActivity.objects
                                                                .get_or_create(block=block,
                                                                               activity=activity))

                    fields = [
                        "rooms",
                        "capacity",
                        "sponsors",
                        "title",
                        "comments",
                        "admin_comments"
                    ]
                    for field_name in fields:
                        setattr(instance, field_name, form.cleaned_data[field_name])

                    # Uncancel if this activity/block pairing was already
                    # created and cancelled
                    if not form["scheduled"].value():
                        instance.cancelled = True
                        instance.cancel()
                    else:
                        instance.cancelled = False
                        instance.uncancel()
                    instance.save()
                else:
                    # Instead of deleting and messing up attendance,
                    # cancel the scheduled activity if it was unscheduled
                    schact = EighthScheduledActivity.objects.filter(
                        block=block,
                        activity=activity
                    )
                    logger.debug(block)
                    logger.debug(activity)
                    logger.debug(schact)
                    # If a both blocks activity, unschedule the other
                    # scheduled activities of it on the same day.
                    if schact and activity.both_blocks:
                        all_sched_act = (EighthScheduledActivity.objects
                                                                .filter(block__date=block.date, activity=activity))
                        logger.debug(all_sched_act)
                        for s in all_sched_act:
                            s.cancelled = True
                            s.cancel()
                            s.save()
                    else:
                        schact.update(cancelled=True)
                        for s in schact:
                            s.cancel()

            messages.success(request, "Successfully updated schedule.")

            # Force reload everything from the database to reset
            # forms that weren't saved
            return redirect(request.get_full_path())
        else:
            messages.error(request, "Error updating schedule.")

    activities = EighthActivity.undeleted_objects.order_by("name")
    activity_id = request.GET.get("activity", None)
    activity = None

    if activity_id is not None and len(activity_id) > 0:
        try:
            activity = EighthActivity.undeleted_objects.get(id=activity_id)
        except (EighthActivity.DoesNotExist, ValueError):
            pass

    all_sponsors = {s["id"]: s for s in EighthSponsor.objects.values()}
    all_rooms = {r["id"]: r for r in EighthRoom.objects.values()}

    for sid, sponsor in all_sponsors.items():
        if sponsor["show_full_name"]:
            all_sponsors[sid]["full_name"] = sponsor["last_name"] + ", " + sponsor["first_name"]
        else:
            all_sponsors[sid]["full_name"] = sponsor["last_name"]

    for rid, room in all_rooms.items():
        all_rooms[rid]["description"] = room["name"] + " (" + str(room["capacity"]) + ")"

    all_signups = {}
    all_default_capacities = {}

    context = {
        "activities": activities,
        "activity": activity,
        "sponsors": all_sponsors,
        "all_signups": all_signups,
        "rooms": all_rooms,
        "sponsors_json": safe_json(all_sponsors),
        "rooms_json": safe_json(all_rooms)
    }

    if activity is not None:
        start_date = get_start_date(request)
        end_date = start_date + timedelta(days=60)

        blocks = EighthBlock.objects.filter(date__gte=start_date, date__lte=end_date)
        initial_formset_data = []

        sched_act_queryset = (EighthScheduledActivity.objects
                                                     .filter(activity=activity)
                                                     .select_related("block")
                                                     .prefetch_related("rooms",
                                                                       "sponsors",
                                                                       "members"))
        all_sched_acts = {sa.block.id: sa for sa in sched_act_queryset}

        for block in blocks:
            initial_form_data = {
                "block": block,
                "activity": activity
            }
            try:
                sched_act = all_sched_acts[block.id]

                all_signups[block.id] = sched_act.members.count()
                all_default_capacities[block.id] = sched_act.get_true_capacity()
                initial_form_data.update({
                    "rooms": sched_act.rooms.all(),
                    "capacity": sched_act.capacity,
                    "sponsors": sched_act.sponsors.all(),
                    "title": sched_act.title,
                    "comments": sched_act.comments,
                    "admin_comments": sched_act.admin_comments,
                    "scheduled": not sched_act.cancelled,
                    "cancelled": sched_act.cancelled
                })
            except KeyError:
                all_signups[block.id] = 0
                all_default_capacities[block.id] = activity.capacity()
                pass
            initial_formset_data.append(initial_form_data)

        if request.method != "POST":
            # There must be an error in the form if this is reached
            formset = ScheduledActivityFormset(initial=initial_formset_data)
        context["formset"] = formset
        context["rows"] = list(zip(blocks, formset))

        context["default_rooms"] = activity.rooms.all()
        context["default_sponsors"] = activity.sponsors.all()
        context["default_capacities"] = all_default_capacities

    context["admin_page_title"] = "Schedule an Activity"
    return render(request, "eighth/admin/schedule_activity.html", context)


@eighth_admin_required
def show_activity_schedule_view(request):
    activities = EighthActivity.undeleted_objects.order_by("name")
    activity_id = request.GET.get("activity", None)
    activity = None

    if activity_id is not None:
        try:
            activity = EighthActivity.undeleted_objects.get(id=activity_id)
        except (EighthActivity.DoesNotExist, ValueError):
            pass

    context = {
        "activities": activities,
        "activity": activity
    }

    if activity is not None:
        start_date = get_start_date(request)
        scheduled_activities = (activity.eighthscheduledactivity_set
                                        .filter(block__date__gte=start_date)
                                        .order_by("block__date",
                                                  "block__block_letter"))
        context["scheduled_activities"] = scheduled_activities

    context["admin_page_title"] = "View Activity Schedule"
    return render(request, "eighth/admin/view_activity_schedule.html", context)


@eighth_admin_required
def distribute_students_view(request):
    context = {}
    return render(request, "eighth/admin/distribute_students.html", context)


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
        if step in ("block_1", "block_2"):
            kwargs.update({
                "exclude_before_date": get_start_date(self.request)
            })
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

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminTransferStudentsWizard,
                        self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Transfer Students"})
        return context

    def done(self, form_list, **kwargs):
        source_block = form_list[0].cleaned_data["block"]
        source_activity = form_list[1].cleaned_data["activity"]
        source_scheduled_activity = EighthScheduledActivity.objects.get(
            block=source_block,
            activity=source_activity
        )

        dest_block = form_list[2].cleaned_data["block"]
        dest_activity = form_list[3].cleaned_data["activity"]
        dest_scheduled_activity = EighthScheduledActivity.objects.get(
            block=dest_block,
            activity=dest_activity
        )

        req = "source_act={}&dest_act={}".format(source_scheduled_activity.id, dest_scheduled_activity.id)

        return redirect("/eighth/admin/scheduling/transfer_students_action?" + req)

transfer_students_view = eighth_admin_required(
    EighthAdminTransferStudentsWizard.as_view(
        EighthAdminTransferStudentsWizard.FORMS
    )
)

@eighth_admin_required
def transfer_students_action(request):
    """ Do the actual process of transferring students. """
    if "source_act" in request.GET:
        source_act = EighthScheduledActivity.objects.get(id=request.GET.get("source_act"))
    elif "source_act" in request.POST:
        source_act = EighthScheduledActivity.objects.get(id=request.POST.get("source_act"))
    else:
        raise Http404

    if "dest_act" in request.GET:
        dest_act = EighthScheduledActivity.objects.get(id=request.GET.get("dest_act"))
    elif "dest_act" in request.POST:
        dest_act = EighthScheduledActivity.objects.get(id=request.POST.get("dest_act"))
    else:
        raise Http404

    num = source_act.members.count()

    context = {
        "admin_page_title": "Transfer Students",
        "source_act": source_act,
        "dest_act": dest_act,
        "num": num
    }

    if request.method == "POST":
        source_act.eighthsignup_set.update(
            scheduled_activity=dest_act
        )
        messages.success(request, "Successfully transfered {} students.".format(num))
        return redirect("eighth_admin_dashboard")
    else:
        return render(request, "eighth/admin/transfer_students.html", context)
