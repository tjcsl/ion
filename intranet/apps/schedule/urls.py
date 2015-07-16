# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    # Admin
    url(r"^$", views.admin_home_view, name="schedule_admin"),
    url(r"^/view$", views.schedule_view, name="schedule"),
    url(r"^/daytype(?:/(?P<id>\d+))?$", views.admin_daytype_view, name="schedule_daytype"),
    url(r"^/add$", views.admin_add_view, name="schedule_add"),

]
