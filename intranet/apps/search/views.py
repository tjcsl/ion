import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from ...utils.helpers import is_entirely_digit
from ..announcements.models import Announcement
from ..auth.decorators import deny_restricted
from ..eighth.models import EighthActivity
from ..events.models import Event
from ..search.utils import get_query
from ..users.models import Course, Grade
from ..users.views import profile_view

logger = logging.getLogger(__name__)


def query(q, admin=False):
    # If only a digit, search for student ID and user ID
    results = []
    if is_entirely_digit(q):
        results = list(get_user_model().objects.exclude_from_search().filter(Q(student_id=q) | Q(id=q)))
    elif ":" in q or ">" in q or "<" in q or "=" in q:
        # A mapping between search keys and LDAP entires
        map_attrs = {
            "firstname": ("first_name", "nickname"),
            "first": ("first_name", "nickname"),
            "lastname": ("last_name",),
            "last": ("last_name",),
            "nick": ("nickname",),
            "nickname": ("nickname",),
            "name": ("last_name", "middle_name", "first_name", "nickname"),
            "middlename": ("middle_name",),
            "middle": ("middle_name",),
            "grade": ("graduation_year",),
            "gradyear": ("graduation_year",),
            "email": ("emails__address",),
            "studentid": ("student_id",),
            "sex": ("gender",),
            "gender": ("gender",),
            "id": ("id",),
            "username": ("username",),
            "counselor": ("counselor__last_name",),
            "type": ("user_type",),
        }

        parts = q.split(" ")
        # split each word
        search_query = Q(pk__gte=-1)  # Initial query that selects all to avoid an empty Q() object.
        for p in parts:
            # Check for less than/greater than, and replace =
            sep = "__icontains"
            if ":" in p:
                cat, val = p.split(":")
                sep = "__icontains"
            elif "=" in p:
                cat, val = p.split("=")
                sep = "__icontains"
            elif "<" in p:
                cat, val = p.split("<")
                sep = "__lte"
            elif ">" in p:
                cat, val = p.split(">")
                sep = "__gte"
            else:
                # Fall back on regular searching (there's no key)

                # Wildcards are already implied at the start and end
                if p.endswith("*"):
                    p = p[:-1]
                if p.startswith("*"):
                    p = p[1:]

                exact = False
                if p.startswith('"') and p.endswith('"'):
                    exact = True
                    p = p[1:-1]

                if not p:
                    continue

                default_categories = ["first_name", "last_name", "nickname"]
                if is_entirely_digit(p):
                    default_categories.append("id")
                if admin:
                    default_categories.append("middle_name")

                sub_query = Q(pk=-1)
                if exact:
                    # No implied wildcard
                    for cat in default_categories:
                        sub_query |= Q(**{"{}__iexact".format(cat): p})

                else:
                    # Search firstname, lastname, uid, nickname (+ middlename if admin) with
                    # implied wildcard at beginning and end of the search
                    # string
                    for cat in default_categories:
                        sub_query |= Q(**{"{}__icontains".format(cat): p})
                search_query &= sub_query

                continue  # skip rest of processing

            if val.startswith('"') and val.endswith('"'):
                # Already exact
                val = val[1:-1]

            cat = cat.lower()
            val = val.lower()

            # fix grade, because LDAP only stores graduation year
            if cat == "grade" and is_entirely_digit(val):
                val = "{}".format(Grade.year_from_grade(int(val)))
            elif cat == "grade" and val == "staff":
                cat = "type"
                val = "teacher"
            elif cat == "grade" and val == "student":
                cat = "type"
                val = "student"

            if cat == "type" and val == "teacher":
                val = "teacher"
            elif cat == "type" and val == "student":
                val = "student"

            # replace sex:male with sex:m and sex:female with sex:f
            if cat in ("sex", "gender"):
                val = val[:1] == "m"

            # if an invalid key, ignore
            if cat not in map_attrs:
                continue

            attrs = map_attrs[cat]

            # for each of the possible LDAP fields, add to the search query
            sub_query = Q(pk=-1)
            for attr in attrs:
                sub_query |= Q(**{"{}{}".format(attr, sep): val})
            search_query &= sub_query

        results = list(get_user_model().objects.exclude_from_search().filter(search_query))
    else:
        # Non-advanced search; no ":"
        parts = q.split(" ")
        # split on each word
        search_query = Q(pk__gte=-1)  # Initial query containing all objects to avoid an empty Q() object.
        for p in parts:
            exact = False
            if p.startswith('"') and p.endswith('"'):
                exact = True
                p = p[1:-1]
            default_categories = ["first_name", "last_name", "nickname", "username"]
            if is_entirely_digit(p):
                default_categories += ["student_id", "id"]
            if admin:
                default_categories.append("middle_name")
            sub_query = Q(pk=-1)
            if exact:
                # No implied wildcard
                for cat in default_categories:
                    sub_query |= Q(**{"{}__iexact".format(cat): p})
            else:
                if p.endswith("*"):
                    p = p[:-1]
                if p.startswith("*"):
                    p = p[1:]
                # Search for first, last, middle, nickname uid, with implied
                # wildcard at beginning and end
                for cat in default_categories:
                    sub_query |= Q(**{"{}__icontains".format(cat): p})
            search_query &= sub_query

            results = list(get_user_model().objects.exclude_from_search().filter(search_query))

    # loop through the DNs saved and get actual user objects
    users = []
    for user in results:
        if user.is_active and user not in users:
            users.append(user)

    return users


def get_search_results(q, admin=False):
    q = q.replace("+", " ")
    users = []

    for qu in q.split(" OR "):
        try:
            users += query(qu, admin)
        except ValueError:
            return "Invalid query", []

    return False, users


def do_activities_search(q):
    filter_query = get_query(q, ["name", "description"])
    entires = EighthActivity.objects.filter(filter_query).order_by("name")
    final_entires = []
    for e in entires:
        if e.is_active:
            final_entires.append(e)
    return final_entires


def do_courses_search(q):
    filter_query = get_query(q, ["name", "course_id"])
    return Course.objects.filter(filter_query).order_by("name")


def do_announcements_search(q):
    filter_query = get_query(q, ["title"])
    entires = Announcement.objects.filter(filter_query).order_by("title")
    final_entires = []
    for e in entires:
        if e.is_this_year:
            final_entires.append(e)
    return final_entires


def do_events_search(q):
    filter_query = get_query(q, ["title"])
    entires = Event.objects.filter(filter_query).order_by("title")
    final_entires = []
    for e in entires:
        if e.is_this_year:
            final_entires.append(e)
    return final_entires


@login_required
@deny_restricted
def search_view(request):
    q = request.GET.get("q", "").strip()
    is_admin = not request.user.is_student and request.user.is_eighthoffice

    if q:
        """User search."""
        if is_entirely_digit(q) and (len(str(q)) == settings.FCPS_STUDENT_ID_LENGTH):
            # Match exact student ID if the input looks like an ID
            u = get_user_model().objects.user_with_student_id(q)
            if u is not None:
                return profile_view(request, user_id=u.id)

        query_error, users = get_search_results(q, request.user.is_eighthoffice)
        if query_error:
            users = []

        if is_admin:
            users = sorted(users, key=lambda u: (u.last_name, u.first_name))

        activities = do_activities_search(q)
        announcements = do_announcements_search(q)
        events = do_events_search(q)
        classes = do_courses_search(q)

        if users and len(users) == 1:
            no_other_results = not activities and not announcements
            if request.user.is_eighthoffice or no_other_results:
                user_id = users[0].id
                return redirect("user_profile", user_id=user_id)

        context = {
            "query_error": query_error,
            "search_query": q,
            "search_results": users,  # User objects
            "announcements": announcements,  # Announcement objects
            "events": events,  # Event objects
            "activities": activities,  # EighthActivity objects
            "classes": classes,  # Course objects
        }
    else:
        context = {"search_results": None}
    context["is_admin"] = is_admin
    return render(request, "search/search_results.html", context)
