# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity
from ..utils import get_start_date
from ....utils.serialization import safe_json

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


@login_required
def statistics_view(request, activity_id=None):
    if not (request.user.is_eighth_admin or request.user.is_teacher):
        return render(request, "error/403.html", {"reason": "You do not have permission to view statistics for this activity."}, status=403)

    activity = get_object_or_404(EighthActivity, id=activity_id)

    activities = EighthScheduledActivity.objects.filter(activity=activity)

    signups = {}
    chart_data = {}

    old_blocks = 0
    cancelled_blocks = 0
    empty_blocks = 0

    start_date = get_start_date(request)
    past_start_date = 0

    for a in activities:
        if a.cancelled:
            cancelled_blocks += 1
        elif a.block.is_this_year:
            if a.block.date > start_date:
                past_start_date += 1
                continue
            members = a.members.count()
            for user in a.members.all():
                if user in signups:
                    signups[user] += 1
                else:
                    signups[user] = 1
            if str(a.block.date) not in chart_data:
                chart_data[str(a.block.date)] = {}
            chart_data[str(a.block.date)][str(a.block.block_letter)] = members
            if members == 0 and not a.cancelled:
                empty_blocks += 1
        else:
            old_blocks += 1

    signups = sorted(signups.items(), key=lambda kv: (-kv[1], kv[0].username))
    total_blocks = activities.count()
    scheduled_blocks = total_blocks - cancelled_blocks
    total_signups = sum(n for _, n in signups)
    if scheduled_blocks:
        average_signups = round(total_signups / scheduled_blocks, 2)
    else:
        average_signups = 0

    context = {"activity": activity,
               "members": signups,
               "total_blocks": total_blocks,
               "total_signups": total_signups,
               "average_signups": average_signups,
               "old_blocks": old_blocks,
               "cancelled_blocks": cancelled_blocks,
               "scheduled_blocks": scheduled_blocks,
               "empty_blocks": empty_blocks,
               "capacity": activities[total_blocks - 1].get_true_capacity() if total_blocks > 0 else 0,
               "chart_data": safe_json(chart_data),
               "past_start_date": past_start_date}
    return render(request, "eighth/statistics.html", context)
