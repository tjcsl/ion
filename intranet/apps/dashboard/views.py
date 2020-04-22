import logging
from datetime import timedelta
from itertools import chain

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from ...utils.date import get_senior_graduation_date, get_senior_graduation_year
from ...utils.helpers import get_ap_week_warning, get_fcps_emerg
from ..announcements.models import Announcement, AnnouncementRequest
from ..eighth.models import EighthBlock, EighthScheduledActivity, EighthSignup
from ..events.models import Event, TJStarUUIDMap
from ..schedule.views import decode_date, schedule_context
from ..seniors.models import Senior

logger = logging.getLogger(__name__)


def gen_schedule(user, num_blocks=6, surrounding_blocks=None):
    """Generate a list of information about a block and a student's current activity signup.

    Returns:
        schedule
        no_signup_today

    """
    no_signup_today = None
    schedule = []

    if surrounding_blocks is None:
        surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

    if not surrounding_blocks:
        return None, False

    # Use select_related to reduce query count
    signups = EighthSignup.objects.filter(user=user, scheduled_activity__block__in=surrounding_blocks).select_related(
        "scheduled_activity", "scheduled_activity__block", "scheduled_activity__activity"
    )
    block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

    for b in surrounding_blocks:
        current_sched_act = block_signup_map.get(b.id, None)
        if current_sched_act:
            current_signup = current_sched_act.title_with_flags
            current_signup_cancelled = current_sched_act.cancelled
            current_signup_sticky = current_sched_act.activity.sticky
            rooms = current_sched_act.get_true_rooms()
        else:
            current_signup = None
            current_signup_cancelled = False
            current_signup_sticky = False
            rooms = None

        # warning flag (red block text and signup link) if no signup today
        # cancelled flag (red activity text) if cancelled
        flags = "locked" if b.locked else "open"
        blk_today = b.is_today()
        if blk_today and not current_signup:
            flags += " warning"
        if current_signup_cancelled:
            flags += " cancelled warning"

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
            "signup_time_future": b.signup_time_future(),
            "rooms": rooms,
        }
        schedule.append(info)

        if blk_today and not current_signup:
            no_signup_today = True

    return schedule, no_signup_today


def gen_sponsor_schedule(user, sponsor=None, num_blocks=6, surrounding_blocks=None, given_date=None):
    r"""Return a list of :class:`EighthScheduledActivity`\s in which the
    given user is sponsoring.

    Returns:
        Dictionary with:
            activities
            no_attendance_today
            num_acts
    """

    no_attendance_today = None
    acts = []

    if sponsor is None:
        sponsor = user.get_eighth_sponsor()

    if surrounding_blocks is None:
        surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

    activities_sponsoring = EighthScheduledActivity.objects.for_sponsor(sponsor).select_related("block").filter(block__in=surrounding_blocks)
    sponsoring_block_map = {}
    for sa in activities_sponsoring:
        bid = sa.block.id
        if bid in sponsoring_block_map:
            sponsoring_block_map[bid] += [sa]
        else:
            sponsoring_block_map[bid] = [sa]

    num_acts = 0

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
            acts.append({"block": b, "id": None, "fake": True})
        else:
            num_acts += 1

    cur_date = surrounding_blocks[0].date if acts else given_date if given_date else timezone.localdate()

    last_block = surrounding_blocks[len(surrounding_blocks) - 1] if surrounding_blocks else None
    last_block_date = last_block.date + timedelta(days=1) if last_block else cur_date
    next_blocks = list(last_block.next_blocks(1)) if last_block else None
    next_date = next_blocks[0].date if next_blocks else last_block_date  # pylint: disable=unsubscriptable-object

    first_block = surrounding_blocks[0] if surrounding_blocks else None
    if cur_date and not first_block:
        first_block = EighthBlock.objects.filter(date__lte=cur_date).last()
    first_block_date = first_block.date + timedelta(days=-7) if first_block else cur_date
    prev_blocks = list(first_block.previous_blocks(num_blocks - 1)) if first_block else None
    prev_date = prev_blocks[0].date if prev_blocks else first_block_date  # pylint: disable=unsubscriptable-object
    return {
        "sponsor_schedule": acts,
        "no_attendance_today": no_attendance_today,
        "num_attendance_acts": num_acts,
        "sponsor_schedule_cur_date": cur_date,
        "sponsor_schedule_next_date": next_date,
        "sponsor_schedule_prev_date": prev_date,
    }


def get_prerender_url(request):
    if request.user.is_eighth_admin:
        if request.user.is_student:
            view = "eighth_signup"
        else:
            view = "eighth_admin_dashboard"
    else:
        view = "eighth_redirect"

    return request.build_absolute_uri(reverse(view))


def get_announcements_list(request, context):
    """
    An announcement will be shown if:
    * It is not expired

      * unless ?show_expired=1

    * It is visible to the user

      * There are no groups on the announcement (so it is public)
      * The user's groups are in union with the groups on the
        announcement (at least one matches)
      * The user submitted the announcement directly
      * The user submitted the announcement through a request
      * The user approved the announcement through a request
      * ...unless ?show_all=1

    An event will be shown if:
    * It is not expired

      * unless ?show_expired=1

    * It is approved

      * unless an events admin

    * It is visible to the user

      * There are no groups
      * The groups are in union

    """
    user = context["user"]

    if context["announcements_admin"] and context["show_all"]:
        # Show all announcements if user has admin permissions and the
        # show_all GET argument is given.
        announcements = Announcement.objects.all()
    else:
        # Only show announcements for groups that the user is enrolled in.
        if context["show_expired"]:
            announcements = Announcement.objects.visible_to_user(user)
        else:
            announcements = Announcement.objects.visible_to_user(user).filter(expiration_date__gt=timezone.now())

    # Load information on the user who posted the announcement
    # Unless the announcement has a custom author (some do, but not all), we will need the user information to construct the byline,
    announcements = announcements.select_related("user")

    # We may query the announcement request multiple times while checking if the user submitted or approved the announcement.
    # prefetch_related() will still make a separate query for each request, but the results are cached if we check them multiple times
    announcements = announcements.prefetch_related("announcementrequest_set")

    if context["events_admin"] and context["show_all"]:
        events = Event.objects.all()
    else:
        if context["show_expired"]:
            events = Event.objects.visible_to_user(user)
        else:
            # Unlike announcements, show events for the rest of the day after they occur.
            midnight = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
            events = Event.objects.visible_to_user(user).filter(time__gte=midnight, show_on_dashboard=True)

    items = sorted(chain(announcements, events), key=lambda item: (item.pinned, item.added))
    items.reverse()

    return items


def paginate_announcements_list(request, context, items):
    """
    ***TODO*** Migrate to django Paginator (see lostitems)

    """

    # pagination
    if "start" in request.GET:
        try:
            start_num = int(request.GET.get("start"))
        except ValueError:
            start_num = 0
    else:
        start_num = 0

    display_num = 10
    end_num = start_num + display_num
    prev_page = start_num - display_num
    more_items = (len(items) - start_num) > display_num
    try:
        items_sorted = items[start_num:end_num]
    except (ValueError, AssertionError):
        items_sorted = items[:display_num]
    else:
        items = items_sorted

    context.update({"items": items, "start_num": start_num, "end_num": end_num, "prev_page": prev_page, "more_items": more_items})

    return context, items


def get_tjstar_mapping(user):
    m = TJStarUUIDMap.objects.filter(user=user)
    if m:
        return {"tjstar_uuid": m.first().uuid}

    return {}


def add_widgets_context(request, context):
    """
    WIDGETS:
    * Eighth signup (STUDENT)
    * Eighth attendance (TEACHER or ADMIN)
    * Bell schedule (ALL)
    * Administration (ADMIN)
    * Links (ALL)
    * Seniors (STUDENT; graduation countdown if senior, link to destinations otherwise)
    """

    user = context["user"]
    if context["is_student"] or context["eighth_sponsor"]:
        num_blocks = 6
        surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

    if context["is_student"]:
        schedule, no_signup_today = gen_schedule(user, num_blocks, surrounding_blocks)
        context.update(
            {
                "schedule": schedule,
                "last_displayed_block": schedule[-1] if schedule else None,
                "no_signup_today": no_signup_today,
                "senior_graduation": get_senior_graduation_date().strftime("%B %d %Y %H:%M:%S"),
                "senior_graduation_year": get_senior_graduation_year(),
            }
        )

    if context["eighth_sponsor"]:
        sponsor_date = request.GET.get("sponsor_date", None)
        if sponsor_date:
            sponsor_date = decode_date(sponsor_date)
            if sponsor_date:
                block = EighthBlock.objects.filter(date__gte=sponsor_date).first()
                if block:
                    surrounding_blocks = [block] + list(block.next_blocks(num_blocks - 1))
                else:
                    surrounding_blocks = []

        sponsor_sch = gen_sponsor_schedule(user, context["eighth_sponsor"], num_blocks, surrounding_blocks, sponsor_date)
        context.update(sponsor_sch)
        # "sponsor_schedule", "no_attendance_today", "num_attendance_acts",
        # "sponsor_schedule_cur_date", "sponsor_schedule_prev_date", "sponsor_schedule_next_date"

    sched_ctx = schedule_context(request)
    context.update(sched_ctx)

    return context


@login_required
def dashboard_view(request, show_widgets=True, show_expired=False, ignore_dashboard_types=None, show_welcome=False):
    """Process and show the dashboard, which includes activities, events, and widgets."""

    user = request.user

    announcements_admin = user.has_admin_permission("announcements")
    events_admin = user.has_admin_permission("events")

    if not show_expired:
        show_expired = "show_expired" in request.GET

    show_all = request.GET.get("show_all", "0") != "0"
    if "show_all" not in request.GET and request.user.is_eighthoffice:
        # Show all by default to 8th period office
        show_all = True

    # Include show_all postfix on next/prev links
    paginate_link_suffix = "&show_all=1" if show_all else ""
    is_index_page = request.path_info in ["/", ""]

    context = {
        "prerender_url": get_prerender_url(request),
        "user": user,
        "announcements_admin": announcements_admin,
        "events_admin": events_admin,
        "is_index_page": is_index_page,
        "show_all": show_all,
        "paginate_link_suffix": paginate_link_suffix,
        "show_expired": show_expired,
    }

    # Get list of announcements
    items = get_announcements_list(request, context)

    # Paginate announcements list
    context, items = paginate_announcements_list(request, context, items)

    user_hidden_announcements = Announcement.objects.hidden_announcements(user).values_list("id", flat=True)
    user_hidden_events = Event.objects.hidden_events(user).values_list("id", flat=True)

    if ignore_dashboard_types is None:
        ignore_dashboard_types = []

    context.update(
        {
            "hide_announcements": True,
            "hide_events": True,
            "user_hidden_announcements": user_hidden_announcements,
            "user_hidden_events": user_hidden_events,
            "ignore_dashboard_types": ignore_dashboard_types,
        }
    )

    is_student = user.is_student
    is_teacher = user.is_teacher
    is_senior = user.is_senior
    is_global_admin = user.member_of("admin_all") and user.is_superuser
    show_admin_widget = is_global_admin or announcements_admin or user.is_eighth_admin
    eighth_sponsor = user.get_eighth_sponsor()

    # the URL path for forward/back buttons
    view_announcements_url = "index"

    if show_widgets:
        dashboard_title = "Dashboard"
        dashboard_header = "Dashboard"
    elif show_expired:
        dashboard_title = dashboard_header = "Announcement Archive"
        view_announcements_url = "announcements_archive"
    else:
        dashboard_title = dashboard_header = "Announcements"

    num_senior_destinations = len(Senior.objects.filled())

    try:
        dash_warning = settings.DASH_WARNING
    except Exception:
        dash_warning = None

    fcps_emerg = get_fcps_emerg(request)
    ap_week = get_ap_week_warning(request)
    if fcps_emerg:
        dash_warning = fcps_emerg
    elif ap_week:
        dash_warning = ap_week

    context.update(
        {
            "dash_warning": dash_warning,
            "show_widgets": show_widgets,
            "show_expired": show_expired,
            "view_announcements_url": view_announcements_url,
            "dashboard_title": dashboard_title,
            "dashboard_header": dashboard_header,
            "is_student": is_student,
            "is_teacher": is_teacher,
            "is_senior": is_senior,
            "is_global_admin": is_global_admin,
            "show_admin_widget": show_admin_widget,
            "eighth_sponsor": eighth_sponsor,
            "num_senior_destinations": num_senior_destinations,
        }
    )

    if settings.TJSTAR_MAP:
        context.update(get_tjstar_mapping(request.user))

    if show_widgets:
        context = add_widgets_context(request, context)

    if announcements_admin:
        all_waiting = AnnouncementRequest.objects.filter(posted=None, rejected=False).this_year()
        awaiting_teacher = all_waiting.filter(teachers_approved__isnull=True)
        awaiting_approval = all_waiting.filter(teachers_approved__isnull=False)

        context.update({"awaiting_teacher": awaiting_teacher, "awaiting_approval": awaiting_approval})

    self_awaiting_teacher = AnnouncementRequest.objects.filter(posted=None, rejected=False, teachers_requested=request.user).this_year()
    context.update({"self_awaiting_teacher": self_awaiting_teacher})

    if show_welcome:
        return render(request, "welcome/student.html", context)
    else:
        return render(request, "dashboard/dashboard.html", context)
