# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity
from ...auth.decorators import eighth_admin_required

logger = logging.getLogger(__name__)


@login_required
def activity_view(request, activity_id=None):
    activity = get_object_or_404(EighthActivity, id=activity_id)
    first_block = EighthBlock.objects.get_first_upcoming_block()
    scheduled_activities = EighthScheduledActivity.objects.filter(activity=activity)

    show_all = ("show_all" in request.GET)
    if first_block and not show_all:
        two_months = datetime.now().date() + timedelta(weeks=8)
        scheduled_activities = scheduled_activities.filter(block__date__gte=first_block.date, block__date__lte=two_months)

    scheduled_activities = scheduled_activities.order_by("block__date")

    context = {"activity": activity, "scheduled_activities": scheduled_activities}

    return render(request, "eighth/activity.html", context)


@eighth_admin_required
def statistics_view(request, activity_id=None):
    activity = get_object_or_404(EighthActivity, id=activity_id)

    activities = EighthScheduledActivity.objects.filter(activity=activity)

    signups = {}

    for a in activities:
        for user in a.members.all():
            if user in signups:
                signups[user] += 1
            else:
                signups[user] = 1

    signups = sorted(signups.items(), key=lambda kv: (-kv[1], kv[0].username))
    total_blocks = activities.count()
    total_signups = sum(n for _, n in signups)
    average_signups = round(total_signups / total_blocks, 2)

    context = {"activity": activity, "members": signups, "total_blocks": total_blocks, "total_signups": total_signups, "average_signups": average_signups}
    return render(request, "eighth/statistics.html", context)
