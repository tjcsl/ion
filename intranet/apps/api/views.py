# -*- coding: utf-8 -*-

from collections import OrderedDict

from django.core.urlresolvers import reverse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def perma_reverse(request, view, *args, **kwargs):
    return request.build_absolute_uri(reverse(view, *args, **kwargs))


@api_view(("GET",))
@permission_classes((AllowAny, ))
def api_root(request, format=None):
    """Welcome to the Ion API!

    Documentation is below. <pk\> refers to the unique id of a certain object - this is shown as "id" in most lists and references.

    The general form of the api link (with /api/ assumed to be prepended) is shown, along with an example URL.

    All of the API methods, except for those relating to the Bell Schedule, require authentication.
    """

    views = OrderedDict((
        ("Schedule", {
            "/schedule": ["Get today's schedule", perma_reverse(request, "api_schedule_day_list")],
            "/schedule?page_size=<num>": ["Get the schedule for the next <num> days", "{}?page_size=7".format(perma_reverse(request, "api_schedule_day_list"))],
            "/schedule/<date>": ["Get the schedule for a specific day, in YYYY-MM-DD format", perma_reverse(request, "api_schedule_day_detail", kwargs={"date": "2016-04-04"})],
        }),
        ("Announcements", {
            "/announcements": ["Get announcement list", perma_reverse(request, "api_announcements_list_create")],
            "/announcements/<pk>": ["Get announcement details", perma_reverse(request, "api_announcements_detail", kwargs={"pk": 2999})],
        }),
        ("Emergency Announcements", {
            "/emerg": ["Get FCPS emergency announcements", perma_reverse(request, "api_emerg_status")]
        }),
        ("Profile", {
            "/profile": ["Get current user profile", perma_reverse(request, "api_user_myprofile_detail")],
            "/profile/<pk>": ["Get specific user profile", perma_reverse(request, "api_user_profile_detail", kwargs={"pk": 489})],
            "/profile/<pk>/picture": ["Get a specific user's profile picture", perma_reverse(request, "api_user_profile_picture_default", kwargs={"pk": 489})]
        }),
        ("Classes", {
            "/classes/<pk>": ["Get class details", perma_reverse(request, "api_user_class_detail", kwargs={"pk": "924016-01"})]
        }),
        ("Search", {
            "/search/<query>": ["Search users", perma_reverse(request, "api_user_search", kwargs={"query": "last:Kim"})]
        }),
        ("Blocks", {
            "/blocks": ["Get block list", perma_reverse(request, "api_eighth_block_list")],
            "/blocks?start_date=<start_date>": ["Get a block list starting on the specified date (in YYYY-MM-DD format).",
                                                "{}?start_date=2015-11-18".format(perma_reverse(request, "api_eighth_block_list"))],
            "/blocks?date=<date>": ["Get a list of blocks only on the specified date (in YYYY-MM-DD format).", "{}?date=2015-11-18".format(perma_reverse(request, "api_eighth_block_list"))],
            "/blocks/<pk>": ["Get a list of activities on a block", perma_reverse(request, "api_eighth_block_detail", kwargs={"pk": 3030})],
        }),
        ("Activities", {
            "/activities": ["Get eighth activity list", perma_reverse(request, "api_eighth_activity_list")],
            "/activities/<pk>": ["Get eighth activity details", perma_reverse(request, "api_eighth_activity_detail", kwargs={"pk": 115})]
        }),
        ("Signups", {
            "/signups/user": ["Get eighth signups for current user, or sign up a user for activity", perma_reverse(request, "api_eighth_user_signup_list_myid")],
            "/signups/user/<user_id>": ["Get eighth signups for specific user", perma_reverse(request, "api_eighth_user_signup_list", kwargs={"user_id": 8889})],
            "/signups/scheduled_activity/<scheduled_activity_id>": ["Get eighth signups for a specific scheduled activity",
                                                                    perma_reverse(request, "api_eighth_scheduled_activity_signup_list", kwargs={"scheduled_activity_id": 889})]
        })
    ))
    return Response(views)
