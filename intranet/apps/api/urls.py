# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from ..announcements import api as announcements_api
from ..eighth.views import api as eighth_api
from ..users import api as users_api
from .views import api_root


urlpatterns = [
    url(r"^$", api_root, name="api_root"),
    url(r"^/announcements$", announcements_api.ListCreateAnnouncement.as_view(), name="api_announcements_list_create"),
    url(r"^/announcements/(?P<pk>[0-9]+)$", announcements_api.RetrieveUpdateDestroyAnnouncement.as_view(), name="api_announcements_detail"),
    url(r"^/blocks$", eighth_api.EighthBlockList.as_view(), name="api_eighth_block_list"),
    url(r"^/blocks/(?P<pk>[0-9]+)$", eighth_api.EighthBlockDetail.as_view(), name="api_eighth_block_detail"),
    url(r"^/classes/(?P<pk>.{6}-.{2})$", users_api.ClassDetail.as_view(), name="api_user_class_detail"),
    url(r"^/search/(?P<query>.+)$", users_api.Search.as_view(), name="api_user_search"),
    url(r"^/activities/(?P<pk>[0-9]+)$", eighth_api.EighthActivityDetail.as_view(), name="api_eighth_activity_detail"),
    url(r"^/profile$", users_api.ProfileDetail.as_view(), name="api_user_myprofile_detail"),
    url(r"^/profile/(?P<pk>[0-9]+)$", users_api.ProfileDetail.as_view(), name="api_user_profile_detail"),
    url(r"^/signups/user$", eighth_api.EighthUserSignupList.as_view(), name="api_eighth_user_signup_list_myid"),
    url(r"^/signups/user/(?P<user_id>[0-9]+)$", eighth_api.EighthUserSignupList.as_view(), name="api_eighth_user_signup_list"),
    url(r"^/signups/scheduled_activity/(?P<scheduled_activity_id>[0-9]+)$", eighth_api.EighthScheduledActivitySignupList.as_view(), name="api_eighth_scheduled_activity_signup_list"),
]
