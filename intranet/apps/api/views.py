from collections import OrderedDict

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.urls import reverse


def perma_reverse(request, view, *args, **kwargs):
    return request.build_absolute_uri(reverse(view, *args, **kwargs))


@api_view(("GET",))
@permission_classes((AllowAny,))
def api_root(request, format=None):  # pylint: disable=redefined-builtin,unused-argument; It doesn't appear we can change this keyword argument name
    r"""Welcome to the Ion API!

    Documentation is below. <pk> refers to the unique id of a certain object - this is shown as "id" in most lists and references.

    The general form of the api link (with /api/ assumed to be prepended) is shown, along with an example URL.

    All of the API methods, except for those relating to the Bell Schedule, require authentication.

    """

    views = OrderedDict(
        (
            (
                "Schedule",
                {
                    "/schedule": ["Get today's schedule", perma_reverse(request, "api_schedule_day_list")],
                    "/schedule?page_size=<num>": [
                        "Get the schedule for the next <num> days",
                        "{}?page_size=7".format(perma_reverse(request, "api_schedule_day_list")),
                    ],
                    "/schedule/<date>": [
                        "Get the schedule for a specific day, in YYYY-MM-DD format",
                        perma_reverse(request, "api_schedule_day_detail", kwargs={"date": "2016-04-04"}),
                    ],
                },
            ),
            (
                "Announcements",
                {
                    "/announcements": ["List announcements", perma_reverse(request, "api_announcements_list_create")],
                    "/announcements/<pk>": ["Get announcement details", perma_reverse(request, "api_announcements_detail", kwargs={"pk": 2999})],
                },
            ),
            ("Emergency Announcements", {"/emerg": ["Get FCPS emergency announcement information", perma_reverse(request, "api_emerg_status")]}),
            (
                "Profile",
                {
                    "/profile": ["Get current user profile", perma_reverse(request, "api_user_myprofile_detail")],
                    "/profile/<pk>": ["Get specific user profile by user ID", perma_reverse(request, "api_user_profile_detail", kwargs={"pk": 489})],
                    "/profile/<username>": [
                        "Get specific user profile by username",
                        perma_reverse(request, "api_user_profile_detail_by_username", kwargs={"username": "2017ewang"}),
                    ],
                    "/profile/<pk>/picture": [
                        "Get a specific user's profile picture by user ID",
                        perma_reverse(request, "api_user_profile_picture_default", kwargs={"pk": 489}),
                    ],
                    "/profile/<username>/picture": [
                        "Get a specific user's profile picture by username",
                        perma_reverse(request, "api_user_profile_picture_default_by_username", kwargs={"username": "2017ewang"}),
                    ],
                },
            ),
            (
                "Search",
                {
                    "/search/<query>": [
                        "Search users (see {}?tips for advanced search documentation)".format(perma_reverse(request, "search")),
                        perma_reverse(request, "api_user_search", kwargs={"query": "last:Kim"}),
                    ]
                },
            ),
            (
                "Blocks",
                {
                    "/blocks": ["List all blocks this year (paginated)", perma_reverse(request, "api_eighth_block_list")],
                    "/blocks?start_date=<start_date>": [
                        "List all blocks starting on the specified date (in YYYY-MM-DD format; paginated)",
                        "{}?start_date=2015-11-18".format(perma_reverse(request, "api_eighth_block_list")),
                    ],
                    "/blocks?date=<date>": [
                        "List all blocks on the specified date (in YYYY-MM-DD format)",
                        "{}?date=2015-11-18".format(perma_reverse(request, "api_eighth_block_list")),
                    ],
                    "/blocks/<pk>": ["Get a list of activities on a block", perma_reverse(request, "api_eighth_block_detail", kwargs={"pk": 3030})],
                },
            ),
            (
                "Activities",
                {
                    "/activities": ["List all eighth period activities", perma_reverse(request, "api_eighth_activity_list")],
                    "/activities/<pk>": [
                        "Get details for a specific eighth period activity (including some scheduling information)",
                        perma_reverse(request, "api_eighth_activity_detail", kwargs={"pk": 115}),
                    ],
                },
            ),
            (
                "Signups",
                {
                    "/signups/user": [
                        "List eighth signups for the current user, or sign up the current user for an activity",
                        perma_reverse(request, "api_eighth_user_signup_list_myid"),
                    ],
                    "/signups/user/<user_id>": [
                        "List eighth signups for a specific user",
                        perma_reverse(request, "api_eighth_user_signup_list", kwargs={"user_id": 8889}),
                    ],
                    "/signups/user/favorites": [
                        "List favorited eighth activities for current user, or toggle whether an activity is favorited",
                        perma_reverse(request, "api_eighth_user_favorites_list_myid"),
                    ],
                    "/signups/scheduled_activity/<scheduled_activity_id>": [
                        "List eighth signups for a specific scheduled activity",
                        perma_reverse(request, "api_eighth_scheduled_activity_signup_list", kwargs={"scheduled_activity_id": 889}),
                    ],
                },
            ),
            (
                "Bus",
                {
                    "/bus": ["Get list of bus routes", perma_reverse(request, "api_bus_list")],
                    "/bus/<pk>": ["Get information about a specific bus route", perma_reverse(request, "api_bus_detail", kwargs={"pk": 3})],
                },
            ),
        )
    )
    return Response(views)
