# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
import logging
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..announcements.models import Announcement, AnnouncementRequest
from ..eighth.models import (
    EighthBlock, EighthSignup, EighthScheduledActivity
)

logger = logging.getLogger(__name__)


def gen_schedule(user, num_blocks=6):
    """Generate a list of information about a block and a student's
    current activity signup.

    """
    no_signup_today = None
    schedule = []

    block = EighthBlock.objects.get_first_upcoming_block()
    if block is None:
        schedule = None
    else:
        surrounding_blocks = [block] + list(block.next_blocks()[:num_blocks-1])
        # Use select_related to reduce query count
        signups = EighthSignup.objects.filter(user=user).select_related("scheduled_activity__block", "scheduled_activity__activity")
        block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

        for b in surrounding_blocks:
            current_sched_act = block_signup_map.get(b.id, None)
            if current_sched_act:
                current_signup = current_sched_act.title_with_flags
                current_signup_cancelled = current_sched_act.cancelled
            else:
                current_signup = None
                current_signup_cancelled = False

            # warning flag (red block text and signup link) if no signup today
            # cancelled flag (red activity text) if cancelled
            flags = "locked" if b.locked else "open"
            if (b.is_today() and not current_signup):
                flags += " warning"
            if current_signup_cancelled:
                flags += " cancelled"

            if current_signup_cancelled:
                # don't duplicate this info; already caught
                current_signup = current_signup.replace(" (Cancelled)", "")

            info = {
                "id": b.id,
                "block": b,
                "block_letter": b.block_letter,
                "current_signup": current_signup,
                "current_signup_cancelled": current_signup_cancelled,
                "locked": b.locked,
                "date": b.date,
                "flags": flags,
                "is_today": b.is_today(),
                "signup_time": b.signup_time,
                "signup_time_future": b.signup_time_future
            }
            schedule.append(info)

            if b.is_today() and not current_signup:
                no_signup_today = True

    return schedule, no_signup_today


def gen_sponsor_schedule(user, num_blocks=6):
    """Return a list of :class:`EighthScheduledActivity`\s in which the
    given user is sponsoring.

    """

    no_attendance_today = None
    acts = []

    sponsor = user.get_eighth_sponsor()

    block = EighthBlock.objects.get_first_upcoming_block()
    if block is None:
        return [], False

    activities_sponsoring = (EighthScheduledActivity.objects.for_sponsor(sponsor)
                                                            .filter(block__date__gte=block.date))

    surrounding_blocks = [block] + list(block.next_blocks()[:num_blocks-1])
    for b in surrounding_blocks:
        num_added = 0
        sponsored_for_block = activities_sponsoring.filter(block=b)

        for schact in sponsored_for_block:
            acts.append(schact)
            if schact.block.is_today():
                if not schact.attendance_taken and schact.block.locked:
                    no_attendance_today = True

            num_added += 1

        if num_added == 0:
            # fake an entry for a block where there is no sponsorship
            acts.append({
                "block": b,
                "id": None,
                "fake": True
            })

    logger.debug(acts)
    return acts, no_attendance_today


@login_required
def dashboard_view(request):
    """Process and show the dashboard."""

    if request.user.has_admin_permission("announcements") and "show_all" in request.GET:
        # Show all announcements if user has admin permissions and the
        # show_all GET argument is given.
        announcements = (Announcement.objects.all()
                                             .prefetch_related("groups"))
    else:
        # Only show announcements for groups that the user is enrolled in.
        announcements = (Announcement.objects
                                     .visible_to_user(request.user)
                                     .filter(expiration_date__gt=timezone.now())
                                     .prefetch_related("groups", "user"))

    # pagination
    if "start" in request.GET:
        start_num = int(request.GET.get("start"))
    else:
        start_num = 0

    display_num = 15
    end_num = start_num + display_num
    more_announcements = ((announcements.count() - start_num) > display_num)
    announcements = announcements[start_num:end_num]

    is_student = request.user.is_student
    eighth_sponsor = request.user.is_eighth_sponsor


    if is_student:
        schedule, no_signup_today = gen_schedule(request.user)
    else:
        schedule = None
        no_signup_today = None

    if eighth_sponsor:
        sponsor_schedule, no_attendance_today = gen_sponsor_schedule(request.user)
    else:
        sponsor_schedule = None
        no_attendance_today = None

    announcements_admin = request.user.has_admin_permission("announcements")
    if announcements_admin:
        all_waiting = AnnouncementRequest.objects.filter(posted=None, rejected=False)
        awaiting_teacher = all_waiting.filter(teachers_approved__isnull=True)
        awaiting_approval = all_waiting.filter(teachers_approved__isnull=False)
    else:
        awaiting_approval = awaiting_teacher = None

    user_hidden_announcements = Announcement.objects.hidden_announcements(request.user)

    context = {
        "announcements": announcements,
        "announcements_admin": announcements_admin,
        "awaiting_teacher": awaiting_teacher,
        "awaiting_approval": awaiting_approval,
        "schedule": schedule,
        "no_signup_today": no_signup_today,
        "sponsor_schedule": sponsor_schedule,
        "no_attendance_today": no_attendance_today,
        "eighth_sponsor": eighth_sponsor,
        "start_num": start_num,
        "end_num": end_num,
        "prev_page": start_num - display_num,
        "more_announcements": more_announcements,
        "hide_announcements": True,
        "user_hidden_announcements": user_hidden_announcements
    }
    return render(request, "dashboard/dashboard.html", context)
