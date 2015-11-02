# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
import logging
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render
from intranet import settings
from ..users.models import User
from ..schedule.views import schedule_context
from ..announcements.models import Announcement, AnnouncementRequest
from ..eighth.models import (
    EighthBlock, EighthSignup, EighthScheduledActivity
)

logger = logging.getLogger(__name__)


def gen_schedule(user, num_blocks=6, surrounding_blocks=None):
    """Generate a list of information about a block and a student's
    current activity signup.

    Returns:
        schedule
        no_signup_today

    """
    no_signup_today = None
    schedule = []

    if surrounding_blocks is None:
        surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

    if len(surrounding_blocks) == 0:
        return None, False

    # Use select_related to reduce query count
    signups = EighthSignup.objects.filter(user=user, scheduled_activity__block__in=surrounding_blocks).select_related("scheduled_activity", "scheduled_activity__block", "scheduled_activity__activity")
    block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

    for b in surrounding_blocks:
        current_sched_act = block_signup_map.get(b.id, None)
        if current_sched_act:
            current_signup = current_sched_act.title_with_flags
            current_signup_cancelled = current_sched_act.cancelled
            current_signup_sticky = current_sched_act.activity.sticky
        else:
            current_signup = None
            current_signup_cancelled = False
            current_signup_sticky = False

        # warning flag (red block text and signup link) if no signup today
        # cancelled flag (red activity text) if cancelled
        flags = "locked" if b.locked else "open"
        blk_today = b.is_today()
        if (blk_today and not current_signup):
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
            "current_signup_sticky": current_signup_sticky,
            "locked": b.locked,
            "date": b.date,
            "flags": flags,
            "is_today": blk_today,
            "signup_time": b.signup_time,
            "signup_time_future": b.signup_time_future
        }
        schedule.append(info)

        if blk_today and not current_signup:
            no_signup_today = True

    return schedule, no_signup_today


def gen_sponsor_schedule(user, sponsor=None, num_blocks=6, surrounding_blocks=None):
    """Return a list of :class:`EighthScheduledActivity`\s in which the
    given user is sponsoring.

    Returns:
        sponsor_schedule
        no_attendance_today
    """

    no_attendance_today = None
    acts = []

    if sponsor is None:
        sponsor = user.get_eighth_sponsor()

    if surrounding_blocks is None:
        surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

    activities_sponsoring = (EighthScheduledActivity.objects.for_sponsor(sponsor)
                                                            .select_related("block")
                                                            .filter(block__in=surrounding_blocks))
    sponsoring_block_map = {}
    for sa in activities_sponsoring:
        bid = sa.block.id
        if bid in sponsoring_block_map:
            sponsoring_block_map[bid] += [sa]
        else:
            sponsoring_block_map[bid] = [sa]

    for b in surrounding_blocks:
        num_added = 0
        sponsored_for_block = sponsoring_block_map.get(b.id, [])

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


def find_birthdays(request):
    """Return information on user birthdays."""
    today = datetime.now().date()
    actual_today = datetime.now().date()
    custom = False
    yr_inc = 0
    if "birthday_month" in request.GET and "birthday_day" in request.GET:
        try:
            mon = int(request.GET["birthday_month"])
            day = int(request.GET["birthday_day"])
            yr = today.year

            """ If searching a date that already happened this year, skip to the next year. """
            if mon < today.month or (mon == today.month and day < today.day):
                yr += 1
                yr_inc = 1

            today = datetime(yr, mon, day).date()
            custom = True
        except Exception:
            pass

    key = "birthdays:{}".format(today)

    cached = cache.get(key)

    if cached:
        logger.debug("Birthdays on {} loaded "
                     "from cache.".format(today))
        logger.debug(cached)
        return cached
    else:
        logger.debug("Loading and caching birthday info for {}".format(today))
        tomorrow = today + timedelta(days=1)

        data = {
            "custom": custom,
            "today": {
                "date": today,
                "users": [{
                    "id": u.id,
                    "full_name": u.full_name,
                    "grade": {
                        "name": u.grade.name
                    },
                    "age": (u.age + yr_inc) if u.age is not None else -1
                } for u in User.objects.users_with_birthday(today.month, today.day)],
                "inc": 0
            },
            "tomorrow": {
                "date": tomorrow,
                "users": [{
                    "id": u.id,
                    "full_name": u.full_name,
                    "grade": {
                        "name": u.grade.name
                    },
                    "age": u.age
                } for u in User.objects.users_with_birthday(tomorrow.month, tomorrow.day)],
                "inc": 1
            }
        }
        cache.set(key, data, timeout=60 * 60 * 24)
        return data


@login_required
def dashboard_view(request, show_widgets=True, show_expired=False):
    """Process and show the dashboard."""

    user = request.user

    announcements_admin = user.has_admin_permission("announcements")

    if not show_expired:
        show_expired = ("show_expired" in request.GET)

    if announcements_admin and "show_all" in request.GET:
        # Show all announcements if user has admin permissions and the
        # show_all GET argument is given.
        announcements = (Announcement.objects.all())
    else:
        # Only show announcements for groups that the user is enrolled in.
        if show_expired:
            announcements = (Announcement.objects
                                     .visible_to_user(user))
        else:
            announcements = (Announcement.objects
                                         .visible_to_user(user)
                                         .filter(expiration_date__gt=timezone.now()))

    # pagination
    if "start" in request.GET:
        try:
            start_num = int(request.GET.get("start"))
        except ValueError:
            start_num = 0
    else:
        start_num = 0

    display_num = 15
    end_num = start_num + display_num
    more_announcements = ((announcements.count() - start_num) > display_num)
    try:
        announcements_sorted = announcements[start_num:end_num]
    except (ValueError, AssertionError):
        announcements_sorted = announcements[:display_num]
    else:
        announcements = announcements_sorted

    announcements = announcements.select_related("user").prefetch_related("groups", "event")

    user_hidden_announcements = (Announcement.objects.hidden_announcements(user)
                                                     .values_list("id", flat=True))

    is_student = user.is_student
    is_teacher = user.is_teacher
    is_senior = (user.grade.number == 12) if user.grade and user.grade.number else False
    eighth_sponsor = user.get_eighth_sponsor()

    if show_widgets:
        dashboard_title = "Dashboard"
        dashboard_header = "Announcements"
    elif show_expired:
        dashboard_title = dashboard_header = "Announcement Archive"
    else:
        dashboard_title = dashboard_header = "Announcements"

    context = {
        "announcements": announcements,
        "announcements_admin": announcements_admin,
        "start_num": start_num,
        "end_num": end_num,
        "prev_page": start_num - display_num,
        "more_announcements": more_announcements,
        "hide_announcements": True,
        "user_hidden_announcements": user_hidden_announcements,
        "show_widgets": show_widgets,
        "show_expired": show_expired,
        "dashboard_title": dashboard_title,
        "dashboard_header": dashboard_header,
        "is_student": is_student,
        "is_teacher": is_teacher,
        "is_senior": is_senior
    }


    if show_widgets:
        if is_student or eighth_sponsor:
            num_blocks = 6
            surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

        if is_student:
            schedule, no_signup_today = gen_schedule(user, num_blocks, surrounding_blocks)
            context.update({
                "schedule": schedule,
                "no_signup_today": no_signup_today,
                "senior_graduation": settings.SENIOR_GRADUATION,
                "senior_graduation_year": settings.SENIOR_GRADUATION_YEAR,
            })

        if eighth_sponsor:
            sponsor_schedule, no_attendance_today = gen_sponsor_schedule(user, eighth_sponsor, num_blocks, surrounding_blocks)
            context.update({
                "sponsor_schedule": sponsor_schedule,
                "no_attendance_today": no_attendance_today
            })

        context.update({
            "eighth_sponsor": eighth_sponsor,
            "birthdays": find_birthdays(request),
            "sched_ctx": schedule_context(request)["sched_ctx"]
        })

    if announcements_admin:
        all_waiting = AnnouncementRequest.objects.filter(posted=None, rejected=False)
        awaiting_teacher = all_waiting.filter(teachers_approved__isnull=True)
        awaiting_approval = all_waiting.filter(teachers_approved__isnull=False)

        context.update({
            "awaiting_teacher": awaiting_teacher,
            "awaiting_approval": awaiting_approval,
        })

    return render(request, "dashboard/dashboard.html", context)
