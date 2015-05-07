# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..announcements.models import Announcement
from ..eighth.models import EighthBlock, EighthSignup

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """Process and show the dashboard."""
    announcements = Announcement.objects.order_by("-updated").all()

    schedule = []

    block = EighthBlock.objects.get_first_upcoming_block()
    if block is None:
        schedule = None
    else:
        surrounding_blocks = block.next_blocks()
        signups = EighthSignup.objects.filter(user=request.user).select_related("scheduled_activity__block", "scheduled_activity__activity")
        block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

        for b in surrounding_blocks:
            info = {
                "id": b.id,
                "block_letter": b.block_letter,
                "current_signup": getattr(block_signup_map.get(b.id, {}), "activity", None),
                "current_signup_cancelled": getattr(block_signup_map.get(b.id, {}), "cancelled", False),
                "locked": b.locked
            }
            day = {}
            day["date"] = b.date
            day["blocks"] = []
            day["blocks"].append(info)
            schedule.append(day)
        
    context = {
        "announcements": announcements,
        "schedule": schedule
    }
    return render(request, "dashboard/dashboard.html", context)
