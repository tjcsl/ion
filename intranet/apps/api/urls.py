# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from ..announcements import api as announcements_api
from ..eighth.views import api as eighth_api
from .views import api_root


urlpatterns = [
    url(r"^$", api_root, name="api_root"),
    url(r"^/announcements$", announcements_api.ListCreateAnnouncement.as_view(), name="api_announcements_list_create"),
    url(r"^/announcements/(?P<pk>[0-9]+)$", announcements_api.RetrieveUpdateDestroyAnnouncement.as_view(), name="api_announcements_detail"),
    url(r"^/blocks$", eighth_api.EighthBlockList.as_view(), name="api_eighth_block_list"),
    url(r"^/blocks/(?P<pk>[0-9]+)$", eighth_api.EighthBlockDetail.as_view(), name="api_eighth_block_detail"),
    url(r"^/activity/(?P<pk>[0-9]+)$", eighth_api.EighthActivityDetail.as_view(), name="api_eighth_activity_detail"),
    url(r"^/signups/user$", eighth_api.EighthUserSignupList.as_view(), name="api_eighth_user_signup_list_myid"),
    url(r"^/signups/user/(?P<user_id>[0-9]+)$", eighth_api.EighthUserSignupList.as_view(), name="api_eighth_user_signup_list"),
    url(r"^/signups/scheduled_activity/(?P<scheduled_activity_id>[0-9]+)$", eighth_api.EighthScheduledActivitySignupList.as_view(), name="api_eighth_scheduled_activity_signup_list"),
]
