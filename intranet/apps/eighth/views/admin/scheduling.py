# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms.formsets import formset_factory
from django.shortcuts import render
from ....auth.decorators import eighth_admin_required
from ...models import EighthBlock, EighthActivity, EighthScheduledActivity
from ...forms.admin.scheduling import ScheduledActivityForm
from ...utils import get_start_date


@eighth_admin_required
def schedule_activity_view(request):
    activities = EighthActivity.objects.order_by("name")
    activity_id = request.GET.get("activity", None)
    activity = None

    if activity_id is not None:
        try:
            activity = EighthActivity.objects.get(id=activity_id)
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
                                                   .get(activity=activity,
                                                        block=block)
                initial_form_data.update({
                    "rooms": sched_act.rooms.all(),
                    "capacity": sched_act.capacity,
                    "sponsors": sched_act.sponsors.all(),
                })
            except EighthScheduledActivity.DoesNotExist:
                initial_form_data.update({
                    "rooms": activity.rooms.all(),
                    "capacity": activity.capacity,
                    "sponsors": activity.sponsors.all()
                })
            initial_formset_data.append(initial_form_data)

        ScheduledActivityFormset = formset_factory(ScheduledActivityForm, extra=0)
        context["formset"] = ScheduledActivityFormset(initial=initial_formset_data)

    return render(request, "eighth/admin/schedule_activity.html", context)
