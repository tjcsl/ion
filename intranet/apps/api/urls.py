from django.conf.urls import url
# from intranet.apps.eighth.views.blocks import EighthBlockList, EighthBlockDetail
# from intranet.apps.eighth.views.activities import EighthActivityDetail
# from intranet.apps.eighth.views.signup import EighthUserSignupList, \
    # EighthScheduledActivitySignupList
from .views import api_root



urlpatterns = [
    url(r"^$", api_root, name="api_root"),
    url(r"^blocks$", EighthBlockList.as_view(), name="api_eighth_block_list"),
    url(r"^blocks/(?P<pk>[0-9]+)$", EighthBlockDetail.as_view(), name="api_eighth_block_detail"),
    url(r"^activities$", EighthActivityList.as_view(), name="api_eighth_activity_list"),
    url(r"^activities/(?P<pk>[0-9]+)$", EighthActivityDetail.as_view(), name="api_eighth_activity_detail"),
    url(r"^signups/user/(?P<user_id>[0-9]+)$", EighthUserSignupList.as_view(), name="api_eighth_user_signup_list"),
    url(r"^signups/scheduled_activity/(?P<scheduled_activity_id>[0-9]+)$", EighthScheduledActivitySignupList.as_view(), name="api_eighth_scheduled_activity_signup_list"),
]
