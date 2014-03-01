from django.conf.urls import patterns, url
from intranet.apps.eighth.views import EighthBlockList, EighthBlockDetail, \
    EighthActivityDetail, EighthUserSignupList, \
    EighthScheduledActivitySignupList, EighthSignupDetail
from .views import api_root

urlpatterns = patterns("",
    url(r"^$", api_root),
    url(r"^blocks$", EighthBlockList.as_view(), name="eighth_block_list"),
    url(r"^blocks/(?P<pk>[0-9]+)$", EighthBlockDetail.as_view(), name="eighth_block_detail"),
    # url(r"^activities$", EighthActivityList.as_view(), name="eighthactivity-list"),
    url(r"^activities/(?P<pk>[0-9]+)$", EighthActivityDetail.as_view(), name="eighth_activity_detail"),
    url(r"^signups/(?P<pk>[0-9]+)$", EighthSignupDetail.as_view(), name="eighth_signup_detail"),
    url(r"^signups/user/(?P<user_id>[0-9]+)$", EighthUserSignupList.as_view(), name="eighth_user_signup_list"),
    url(r"^signups/scheduled_activity/(?P<scheduled_activity_id>[0-9]+)$", EighthScheduledActivitySignupList.as_view(), name="eighth_scheduled_activity_signup_list"),
)
