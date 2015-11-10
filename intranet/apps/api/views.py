# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response


def perma_reverse(request, view, *args, **kwargs):
    return request.build_absolute_uri(reverse(view, *args, **kwargs))


@api_view(("GET",))
def api_root(request, format=None):
    """Welcome to the Ion API!

    Documentation is below. <pk\> refers to the unique id of a certain object - this is shown as "id" in most lists and references.

    The general form of the api link (with /api/ assumed to be prepended) is shown, along with an example URL.
    """

    views = {"Announcements": {
        "/announcements": ["Get announcement list", perma_reverse(request, "api_announcements_list_create")],
        "/announcements/<pk>": ["Get announcement details", perma_reverse(request, "api_announcements_detail", kwargs={"pk": 1234})],
    },
        "Blocks": {
        "/blocks": ["Get block list", perma_reverse(request, "api_eighth_block_list")],
        "/blocks/<pk>": ["Get block details", perma_reverse(request, "api_eighth_block_detail", kwargs={"pk": 1234})],
    },
        "Classes": {
        "/classes/<pk>": ["Get class details", perma_reverse(request, "api_user_class_detail", kwargs={"pk": "123456-78"})]
    },
        "Search": {
        "/search/<query>": ["Search users", perma_reverse(request, "api_user_search", kwargs={"query": "last:Kim"})]
    },
        "Activities": {
        "/activities": ["Get eighth activity list", perma_reverse(request, "api_eighth_activity_list")],
        "/activities/<pk>": ["Get eighth activity details", perma_reverse(request, "api_eighth_activity_detail", kwargs={"pk": 1234})]
    },
        "Profile": {
        "/profile": ["Get current user profile", perma_reverse(request, "api_user_myprofile_detail")],
        "/profile/<pk>": ["Get specific user profile", perma_reverse(request, "api_user_profile_detail", kwargs={"pk": 489})],
        "/profile/<pk>/picture": ["Get a specific user's profile picture", perma_reverse(request, "api_user_profile_picture_default", kwargs={"pk": 489})]
    },
        "Signups": {
        "/signups/user": ["Get eighth signups for current user, or sign up a user for activity", perma_reverse(request, "api_eighth_user_signup_list_myid")],
        "/signups/user/<user_id>": ["Get eighth signups for specific user", perma_reverse(request, "api_eighth_user_signup_list", kwargs={"user_id": 1234})],
        "/signups/scheduled_activity/<scheduled_activity_id>": ["Get eighth signups for a specific scheduled activity", perma_reverse(request, "api_eighth_scheduled_activity_signup_list", kwargs={"scheduled_activity_id": 1234})]
    }
    }
    return Response(views)
