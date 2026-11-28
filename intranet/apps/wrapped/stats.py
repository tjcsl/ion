import datetime
from collections import Counter
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

from ...utils.date import get_date_range_this_year, get_school_year_label
from ..eighth.models import EighthSignup
from ..enrichment.models import EnrichmentActivity
from ..events.models import Event
from ..logs.models import Request
from ..polls.models import Answer, Poll

LAST_MINUTE_WINDOW = datetime.timedelta(minutes=10)
COHORT_CACHE_TIMEOUT = None
RANK_BUCKETS = (0.01, 0.1, 1, 5, 20, 50)


def format_rank_bucket(bucket):
    if bucket < 1:
        return f"{bucket:g}"
    return str(int(bucket))


def as_top_percent(value, values):
    if value <= 0 or not values:
        return None

    values = [v for v in values if v is not None]
    if not values:
        return None

    rank = sum(1 for v in values if v > value) + 1
    return max(0.01, (rank / len(values)) * 100)


def rank_label(top_percent):
    if top_percent is None:
        return None
    for bucket in RANK_BUCKETS:
        if top_percent <= bucket:
            return f"top {format_rank_bucket(bucket)}%"
    return None


def cohort_cache_key(name, start, end):
    return f"wrapped:cohort:v1:{name}:{start.isoformat()}:{end.isoformat()}"


def get_cached_cohort_counts(name, start, end):
    return cache.get(cohort_cache_key(name, start, end))


def set_cached_cohort_counts(name, start, end, counts):
    counts = list(counts)
    cache.set(cohort_cache_key(name, start, end), counts, COHORT_CACHE_TIMEOUT)
    return counts


def student_ids_for_cohort():
    return list(get_user_model().objects.get_students().values_list("id", flat=True))


def compute_signup_counts(start_date, end_date):
    student_ids = student_ids_for_cohort()
    counts_by_user = dict(
        EighthSignup.objects.filter(
            user_id__in=student_ids,
            scheduled_activity__block__date__gte=start_date,
            scheduled_activity__block__date__lte=end_date,
        )
        .values("user_id")
        .annotate(
            wrapped_count=Count("id"),
        )
        .values_list("user_id", "wrapped_count")
    )
    return [counts_by_user.get(student_id, 0) for student_id in student_ids]


def compute_unique_activity_counts(start_date, end_date):
    student_ids = student_ids_for_cohort()
    counts_by_user = dict(
        EighthSignup.objects.filter(
            user_id__in=student_ids,
            scheduled_activity__block__date__gte=start_date,
            scheduled_activity__block__date__lte=end_date,
        )
        .values("user_id")
        .annotate(
            wrapped_count=Count(
                "scheduled_activity__activity",
                distinct=True,
            )
        )
        .values_list("user_id", "wrapped_count")
    )
    return [counts_by_user.get(student_id, 0) for student_id in student_ids]


def compute_visit_counts(start, end):
    student_ids = student_ids_for_cohort()
    counts_by_user = dict(
        Request.objects.filter(user_id__in=student_ids, timestamp__gte=start, timestamp__lte=end, method="GET")
        .exclude(path__startswith="/wrapped")
        .exclude(path__startswith="/api")
        .values("user_id")
        .annotate(wrapped_count=Count("id"))
        .values_list("user_id", "wrapped_count")
    )
    return [counts_by_user.get(student_id, 0) for student_id in student_ids]


def path_area(path):
    clean_path = urlsplit(path).path
    if clean_path in ("", "/"):
        return "Dashboard"
    if clean_path.startswith("/wrapped") or clean_path.startswith("/api"):
        return None

    first = clean_path.strip("/").split("/", maxsplit=1)[0]
    labels = {
        "announcements": "Announcements",
        "bus": "Bus",
        "courses": "Courses",
        "eighth": "8th Period",
        "enrichment": "Enrichment",
        "events": "Events",
        "files": "Files",
        "groups": "Groups",
        "lostfound": "Lost & Found",
        "polls": "Polls",
        "preferences": "Preferences",
        "printing": "Printing",
        "profile": "Profiles",
        "schedule": "Schedule",
        "search": "Search",
        "seniors": "Seniors",
    }
    return labels.get(first, first.replace("-", " ").replace("_", " ").title() or "Dashboard")


def display_list(items):
    return [{"name": name, "count": count} for name, count in items]


def signup_event_times(signups):
    event_times = {signup.id: signup.created_time for signup in signups if signup.id}
    current_scheduled_activities = {signup.id: signup.scheduled_activity_id for signup in signups if signup.id}
    if not current_scheduled_activities:
        return event_times

    previous_scheduled_activities = {}
    history = (
        EighthSignup.history.filter(id__in=current_scheduled_activities.keys())
        .order_by("id", "history_date", "history_id")
        .values("id", "scheduled_activity_id", "history_date")
    )

    for record in history:
        signup_id = record["id"]
        scheduled_activity_id = record["scheduled_activity_id"]
        if (
            scheduled_activity_id == current_scheduled_activities.get(signup_id)
            and previous_scheduled_activities.get(signup_id) != scheduled_activity_id
        ):
            event_times[signup_id] = record["history_date"]
        previous_scheduled_activities[signup_id] = scheduled_activity_id

    return event_times


def build_eighth_stats(user, start_date, end_date):
    signups = (
        EighthSignup.objects.filter(user=user, scheduled_activity__block__date__gte=start_date, scheduled_activity__block__date__lte=end_date)
        .select_related("scheduled_activity__activity", "scheduled_activity__block")
        .prefetch_related(
            "scheduled_activity__activity__rooms",
            "scheduled_activity__rooms",
            "scheduled_activity__activity__sponsors",
            "scheduled_activity__sponsors",
        )
    )

    total = signups.count()
    top_activities = (
        signups.values("scheduled_activity__activity__name").annotate(count=Count("id")).order_by("-count", "scheduled_activity__activity__name")[:3]
    )
    unique_activities = signups.values("scheduled_activity__activity").distinct().count()
    favorites_count = user.favorited_activity_set.count()
    subscriptions_count = user.subscribed_activity_set.count()
    own_signup_count = signups.filter(own_signup=True).count()
    admin_signup_count = max(total - own_signup_count, 0)
    absence_count = signups.filter(was_absent=True, scheduled_activity__attendance_taken=True).count()
    attendance_taken_count = signups.filter(scheduled_activity__attendance_taken=True).count()
    present_count = max(attendance_taken_count - absence_count, 0)

    block_counts = Counter()
    room_counts = Counter()
    sponsor_counts = Counter()
    last_minute_count = 0
    closest_signup = None
    after_deadline_count = 0
    signup_list = list(signups)
    signup_times = signup_event_times(signup_list)

    for signup in signup_list:
        scheduled_activity = signup.scheduled_activity
        block = scheduled_activity.block
        block_counts[block.block_letter] += 1

        deadline = timezone.make_aware(datetime.datetime.combine(block.date, block.signup_time), timezone.get_default_timezone())
        signup_time = signup_times.get(signup.id)
        if signup.after_deadline or (signup_time and signup_time > deadline):
            after_deadline_count += 1
        if signup_time:
            delta = deadline - signup_time
            if datetime.timedelta(0) <= delta <= LAST_MINUTE_WINDOW:
                last_minute_count += 1
            if delta >= datetime.timedelta(0) and (closest_signup is None or delta < closest_signup["delta"]):
                closest_signup = {
                    "delta": delta,
                    "activity": scheduled_activity.full_title,
                    "block": block.short_text,
                }

        rooms = list(scheduled_activity.rooms.all()) or list(scheduled_activity.activity.rooms.all())
        for room in rooms:
            room_counts[room.formatted_name] += 1

        sponsors = list(scheduled_activity.sponsors.all()) or list(scheduled_activity.activity.sponsors.all())
        for sponsor in sponsors:
            sponsor_counts[sponsor.name] += 1

    signup_counts = get_cached_cohort_counts("signup-counts", start_date, end_date)
    unique_counts = get_cached_cohort_counts("unique-activity-counts", start_date, end_date)

    return {
        "total": total,
        "top_activities": display_list((row["scheduled_activity__activity__name"], row["count"]) for row in top_activities),
        "unique_activities": unique_activities,
        "favorites_count": favorites_count,
        "subscriptions_count": subscriptions_count,
        "after_deadline_count": after_deadline_count,
        "own_signup_count": own_signup_count,
        "admin_signup_count": admin_signup_count,
        "absence_count": absence_count,
        "attendance_taken_count": attendance_taken_count,
        "present_count": present_count,
        "top_blocks": display_list(block_counts.most_common(3)),
        "top_rooms": display_list(room_counts.most_common(3)),
        "top_sponsors": display_list(sponsor_counts.most_common(3)),
        "last_minute_count": last_minute_count,
        "closest_signup": closest_signup,
        "signup_percentile": as_top_percent(total, signup_counts),
        "unique_percentile": as_top_percent(unique_activities, unique_counts),
    }


def build_usage_stats(user, start, end):
    visits = (
        Request.objects.filter(user=user, timestamp__gte=start, timestamp__lte=end, method="GET")
        .exclude(path__startswith="/wrapped")
        .exclude(path__startswith="/api")
    )
    total = visits.count()
    area_counts = Counter()
    month_counts = Counter()
    hour_counts = Counter()

    for visit in visits.only("path", "timestamp"):
        area = path_area(visit.path)
        if area:
            area_counts[area] += 1
        local_time = timezone.localtime(visit.timestamp)
        month_counts[local_time.strftime("%B")] += 1
        hour_counts[local_time.hour] += 1

    visit_counts = get_cached_cohort_counts("visit-counts", start, end)

    busiest_hour = None
    if hour_counts:
        hour = hour_counts.most_common(1)[0][0]
        label_hour = datetime.time(hour=hour).strftime("%I %p").lstrip("0")
        busiest_hour = {"name": label_hour, "count": hour_counts[hour]}

    return {
        "total": total,
        "top_areas": display_list(area_counts.most_common(3)),
        "top_month": ({"name": month_counts.most_common(1)[0][0], "count": month_counts.most_common(1)[0][1]} if month_counts else None),
        "busiest_hour": busiest_hour,
        "visit_percentile": as_top_percent(total, visit_counts),
    }


def build_other_stats(user, start, end):
    events_joined = Event.objects.filter(attending=user, time__gte=start, time__lte=end).distinct().count()
    poll_queryset = Poll.objects.filter(start_time__gte=start, start_time__lte=end)
    polls_voted = Poll.objects.filter(question__answer__user=user, start_time__gte=start, start_time__lte=end).distinct().count()
    poll_answers = Answer.objects.filter(user=user, question__poll__in=poll_queryset).count()
    enrichments_joined = EnrichmentActivity.objects.filter(attending=user, time__gte=start, time__lte=end).distinct().count()
    enrichments_attended = EnrichmentActivity.objects.filter(attended=user, time__gte=start, time__lte=end).distinct().count()

    return {
        "events_joined": events_joined,
        "polls_voted": polls_voted,
        "poll_answers": poll_answers,
        "enrichments_joined": enrichments_joined,
        "enrichments_attended": enrichments_attended,
    }


def format_duration(delta):
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if days or hours:
        parts.append(f"{hours}h")
    if days or hours or minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def make_cards(user, year_label, eighth, usage, other):
    top_activity = eighth["top_activities"][0] if eighth["top_activities"] else None
    top_area = usage["top_areas"][0] if usage["top_areas"] else None
    unique_rank = rank_label(eighth["unique_percentile"])
    visit_rank = rank_label(usage["visit_percentile"])

    cards = [
        {
            "eyebrow": f"Ion Wrapped {year_label}",
            "title": f"{user.first_name or user.username}, your Ion wrapped is ready.",
            "body": "A quick recap of your year with Ion: including signups, visits, absences, and more.",
            "stat": "Click to start",
            "variant": "hero",
        },
        {
            "eyebrow": "8th Period Signups",
            "title": "You signed up for",
            "stat": f"{eighth['total']}",
            "unit": "8th periods this year",
            "variant": "green",
        },
        {
            "eyebrow": "Your top 3",
            "title": "These activities saw you the most.",
            "list": eighth["top_activities"],
            "variant": "pink",
        },
        {
            "eyebrow": "Variety",
            "title": "You tried",
            "stat": f"{eighth['unique_activities']}",
            "unit": "different activities this year",
            "body": f"That is {unique_rank} among students." if unique_rank else "Your activity map was compact this year!",
            "variant": "yellow",
        },
        {
            "eyebrow": "Time management",
            "title": "Last-minute signups",
            "stat": f"{eighth['last_minute_count']}",
            "unit": f"within the final {LAST_MINUTE_WINDOW.seconds // 60} minutes",
            "body": (
                f"Your closest call was {format_duration(eighth['closest_signup']['delta'])} before signups closed for {eighth['closest_signup']['activity']}."
                if eighth["closest_signup"]
                else "Congratulations, you had no close calls this year!"
            ),
            "variant": "purple",
        },
        {
            "eyebrow": "Passes & attendance",
            "title": "The official bits",
            "stats": [
                {"label": "after-deadline signups", "value": eighth["after_deadline_count"]},
                {"label": "8th period absences", "value": eighth["absence_count"]},
                {"label": 'times marked "present"', "value": eighth["present_count"]},
            ],
            "body": "Don't worry, we won't tell anyone.",
            "variant": "blue",
        },
        {
            "eyebrow": "Places & people",
            "title": "Your most common rooms and sponsors",
            "columns": [
                {"title": "Rooms", "items": eighth["top_rooms"]},
                {"title": "Sponsors", "items": eighth["top_sponsors"]},
            ],
            "variant": "orange",
        },
        {
            "eyebrow": "Ion visits",
            "title": "You opened Ion",
            "stat": f"{usage['total']}",
            "unit": "times this year",
            "body": f"That lands you in the {visit_rank} for visits." if visit_rank else "Do you even go to TJ?",
            "variant": "green",
        },
        {
            "eyebrow": "Most visited page",
            "title": top_area["name"] if top_area else "No clear favorite",
            "stat": f"{top_area['count']}" if top_area else "",
            "unit": "visits this year" if top_area else "",
            "body": (
                f"Your busiest month was {usage['top_month']['name']}, and your busiest hour was around {usage['busiest_hour']['name']}."
                if usage["top_month"] and usage["busiest_hour"]
                else "The logs kept this one mysterious."
            ),
            "list": usage["top_areas"][1:],
            "variant": "pink",
        },
        {
            "eyebrow": "Around Ion",
            "title": "You left your mark through the rest of Ion.",
            "stats": [
                {"label": "events joined", "value": other["events_joined"]},
                {"label": "polls voted in", "value": other["polls_voted"]},
                {"label": "enrichments joined", "value": other["enrichments_joined"]},
            ],
            "body": "Small clicks, real school year.",
            "variant": "purple",
        },
    ]

    if not top_activity and eighth["total"] == 0:
        cards[2] = {
            "eyebrow": "8th Period",
            "title": "Your activity list is still pretty empty.",
            "body": "Ion Wrapped works best with a signups. Come back later once you've gone to some activities.",
            "stat": "0",
            "unit": "top activities",
            "variant": "pink",
        }

    return cards


def build_wrapped_context(user):
    start, end = get_date_range_this_year()
    eighth = build_eighth_stats(user, start.date(), end.date())
    usage = build_usage_stats(user, start, end)
    other = build_other_stats(user, start, end)
    year_label = get_school_year_label()
    cards = make_cards(user, year_label, eighth, usage, other)

    top_activity = eighth["top_activities"][0]["name"] if eighth["top_activities"] else "No top activity yet"
    top_area = usage["top_areas"][0]["name"] if usage["top_areas"] else "Dashboard"
    share_card = {
        "name": user.first_name or user.username,
        "year": year_label,
        "signups": eighth["total"],
        "top_activity": top_activity,
        "unique_activities": eighth["unique_activities"],
        "last_minute": eighth["last_minute_count"],
        "visits": usage["total"],
        "top_area": top_area,
        "absences": eighth["absence_count"],
        "rank": rank_label(usage["visit_percentile"]) or "Ion regular",
    }

    return {
        "cards": cards,
        "summary": {"year": year_label, "eighth": eighth, "usage": usage, "other": other},
        "share_card": share_card,
        "wrapped_enabled": settings.ENABLE_ION_WRAPPED,
    }
