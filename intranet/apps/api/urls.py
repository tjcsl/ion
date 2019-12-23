from django.urls import re_path

from ..announcements import api as announcements_api
from ..bus import api as bus_api
from ..eighth.views import api as eighth_api
from ..emerg import api as emerg_api
from ..schedule import api as schedule_api
from ..users import api as users_api
from .views import api_root

urlpatterns = [
    re_path(r"^$", api_root, name="api_root"),
    re_path(r"^/announcements$", announcements_api.ListCreateAnnouncement.as_view(), name="api_announcements_list_create"),
    re_path(r"^/announcements/(?P<pk>\d+)$", announcements_api.RetrieveUpdateDestroyAnnouncement.as_view(), name="api_announcements_detail"),
    re_path(r"^/blocks$", eighth_api.EighthBlockList.as_view(), name="api_eighth_block_list"),
    re_path(r"^/blocks/(?P<pk>\d+)$", eighth_api.EighthBlockDetail.as_view(), name="api_eighth_block_detail"),
    re_path(r"^/search/(?P<query>.+)$", users_api.Search.as_view(), name="api_user_search"),
    re_path(r"^/activities$", eighth_api.EighthActivityList.as_view(), name="api_eighth_activity_list"),
    re_path(r"^/activities/(?P<pk>\d+)$", eighth_api.EighthActivityDetail.as_view(), name="api_eighth_activity_detail"),
    re_path(r"^/profile$", users_api.ProfileDetail.as_view(), name="api_user_myprofile_detail"),
    re_path(r"^/profile/(?P<pk>\d+)$", users_api.ProfileDetail.as_view(), name="api_user_profile_detail"),
    re_path(r"^/profile/(?P<username>[A-Za-z\d]+)$", users_api.ProfileDetail.as_view(), name="api_user_profile_detail_by_username"),
    re_path(r"^/profile/(?P<pk>\d+)/picture$", users_api.ProfilePictureDetail.as_view(), name="api_user_profile_picture_default"),
    re_path(
        r"^/profile/(?P<username>[A-Za-z\d]+)/picture$", users_api.ProfilePictureDetail.as_view(), name="api_user_profile_picture_default_by_username"
    ),
    re_path(r"^/profile/(?P<pk>\d+)/picture/(?P<photo_year>[a-zA-Z]+)$", users_api.ProfilePictureDetail.as_view(), name="api_user_profile_picture"),
    re_path(
        r"^/profile/(?P<username>[A-Za-z\d]+)/picture/(?P<photo_year>[a-zA-Z]+)$",
        users_api.ProfilePictureDetail.as_view(),
        name="api_user_profile_picture_by_username",
    ),
    re_path(r"^/signups/user$", eighth_api.EighthUserSignupListAdd.as_view(), name="api_eighth_user_signup_list_myid"),
    re_path(r"^/signups/user/(?P<user_id>\d+)$", eighth_api.EighthUserSignupListAdd.as_view(), name="api_eighth_user_signup_list"),
    re_path(r"^/signups/user/favorites$", eighth_api.EighthUserFavoritesListToggle.as_view(), name="api_eighth_user_favorites_list_myid"),
    re_path(
        r"^/signups/scheduled_activity/(?P<scheduled_activity_id>\d+)$",
        eighth_api.EighthScheduledActivitySignupList.as_view(),
        name="api_eighth_scheduled_activity_signup_list",
    ),
    re_path(r"^/schedule$", schedule_api.DayList.as_view(), name="api_schedule_day_list"),
    re_path(r"^/schedule/(?P<date>.*)$", schedule_api.DayDetail.as_view(), name="api_schedule_day_detail"),
    re_path(r"^/emerg$", emerg_api.emerg_status, name="api_emerg_status"),
    re_path(r"^/bus$", bus_api.RouteList.as_view(), name="api_bus_list"),
    re_path(r"^/bus/(?P<pk>\d+)$", bus_api.RouteDetail.as_view(), name="api_bus_detail"),
]
