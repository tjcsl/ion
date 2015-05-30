# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..announcements.models import Announcement
from ..eighth.models import (
    EighthBlock, EighthSignup, EighthScheduledActivity
)

logger = logging.getLogger(__name__)


def gen_schedule(user, num_blocks=6):
    """Generate a list of information about a block and a student's
    current activity signup.

    """

    schedule = []

    block = EighthBlock.objects.get_first_upcoming_block()
    if block is None:
        schedule = None
    else:
        surrounding_blocks = [block] + list(block.next_blocks()[:num_blocks-1])
        signups = EighthSignup.objects.filter(user=user).select_related("scheduled_activity__block", "scheduled_activity__activity")
        block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

        for b in surrounding_blocks:
            current_sched_act = block_signup_map.get(b.id, {})
            current_signup = getattr(current_sched_act, "activity", None)
            current_signup_cancelled = getattr(current_sched_act, "cancelled", False)

            flags = "locked" if b.locked else "open"
            if (b.is_today() and not current_signup) or current_signup_cancelled:
                flags += " warning"
            if current_signup_cancelled:
                flags += " cancelled"

            info = {
                "id": b.id,
                "block_letter": b.block_letter,
                "block_letter_width": (len(b.block_letter) - 1) * 6 + 15,
                "current_signup": current_signup,
                "current_signup_cancelled": current_signup_cancelled,
                "locked": b.locked,
                "date": b.date,
                "flags": flags
            }
            schedule.append(info)

    return schedule


def gen_sponsor_schedule(user, num_blocks=6):
    """Return a list of :class:`EighthScheduledActivity`\s in which the
    given user is sponsoring.

    """

    acts = []

    sponsor = user.get_eighth_sponsor()

    block = EighthBlock.objects.get_first_upcoming_block()
    activities_sponsoring = EighthScheduledActivity.objects.for_sponsor(sponsor)\
        .filter(block__date__gt=block.date)

    surrounding_blocks = [block] + list(block.next_blocks()[:num_blocks-1])
    for b in surrounding_blocks:
        num_added = 0

        sponsored_for_block = activities_sponsoring.filter(block=b)
        for schact in sponsored_for_block:
            acts.append(schact)
            num_added += 1

        if num_added == 0:
            acts.append({
                "block": b,
                "block_letter_width": (len(b.block_letter) - 1) * 6 + 15,
                "id": None,
                "fake": True
            })

    return acts


@login_required
def dashboard_view(request):
    """Process and show the dashboard."""

    if request.user.has_admin_permission("announcements") and "show_all" in request.GET:
        # Show all announcements if user has admin permissions and the
        # show_all GET argument is given.
        announcements = Announcement.objects.all()
    else:
        # Only show announcements for groups that the user is enrolled in.
        announcements = (Announcement.objects
                                     .visible_to_user(request.user)
                                     .prefetch_related("groups"))

    is_student = request.user.is_student
    eighth_sponsor = request.user.is_eighth_sponsor

    if is_student:
        schedule = gen_schedule(request.user)
    else:
        schedule = None

    if eighth_sponsor:
        sponsor_schedule = gen_sponsor_schedule(request.user)
    else:
        sponsor_schedule = None

    context = {
        "announcements": announcements,
        "schedule": schedule,
        "sponsor_schedule": sponsor_schedule,
        "eighth_sponsor": eighth_sponsor
    }
    return render(request, "dashboard/dashboard.html", context)
