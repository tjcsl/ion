from django.conf.urls import patterns, url
from intranet.apps.eighth.views import EighthBlockList, EighthBlockDetail, EighthActivityList, EighthActivityDetail
from .views import api_root

urlpatterns = patterns("",
                       url(r"^$", api_root),
                       url(r"^blocks/$", EighthBlockList.as_view(), name="eighthblock-list"),
                       url(r"^blocks/(?P<pk>[0-9]+)/$", EighthBlockDetail.as_view(), name="eighthblock-detail"),
                       url(r"^activities/$", EighthActivityList.as_view(), name="eighthactivity-list"),
                       url(r"^activities/(?P<pk>[0-9]+)/$", EighthActivityDetail.as_view(), name="eighthactivity-detail"),
                       )
