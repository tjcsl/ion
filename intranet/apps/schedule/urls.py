# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^$", views.admin_home_view, name="schedule_admin"),
    url(r"^/view$", views.schedule_view, name="schedule"),
    url(r"^/daytype$", views.admin_daytype_view, name="schedule_daytype"),
]
