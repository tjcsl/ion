# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render
from ..announcements.models import Announcement
from ..eighth.models import EighthBlock, EighthSignup

logger = logging.getLogger(__name__)


def get_visible_announcements(user):
    announcements = Announcement.objects.order_by("-updated").all()
    user_announcements = []
    user_groups = user.groups.all()
    for announcement in announcements:
        ann_groups = announcement.groups.all()
        add = False
        for grp in ann_groups:
            if grp in user_groups:
                add = True
        if len(ann_groups) == 0:
            add = True

        if add:
            user_announcements.append(announcement)

    logger.debug("All announcements:")
    logger.debug(announcements)
    logger.debug("User announcements:")
    logger.debug(user_announcements)

    return user_announcements

@login_required
def dashboard_view(request):
    """Process and show the dashboard."""
    
    if request.user.has_admin_permission("announcements") and "show_all" in request.GET:
        announcements = Announcement.objects.order_by("-updated").all()
    else:
        announcements = get_visible_announcements(request.user)

    schedule = []

    num_blocks = 5

    block = EighthBlock.objects.get_first_upcoming_block()
    if block is None:
        schedule = None
    else:
        surrounding_blocks = [block] + list(block.next_blocks()[:num_blocks])
        signups = EighthSignup.objects.filter(user=request.user).select_related("scheduled_activity__block", "scheduled_activity__activity")
        block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

        for b in surrounding_blocks:
            today = ((date.today() - b.date) == timedelta(0))
            info = {
                "id": b.id,
                "block_letter": b.block_letter,
                "current_signup": getattr(block_signup_map.get(b.id, {}), "activity", None),
                "current_signup_cancelled": getattr(block_signup_map.get(b.id, {}), "cancelled", False),
                "locked": b.locked,
                "date": b.date,
                "flags": ("locked" if b.locked else "open" + (" warning" if today else ""))
            }
            logger.debug(info)
            schedule.append(info)
        
    logger.debug(schedule)
    context = {
        "announcements": announcements,
        "schedule": schedule
    }
    return render(request, "dashboard/dashboard.html", context)
