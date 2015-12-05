# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^/display$", views.signage_display, name="signage_display"),
    url(r"^/display/(?P<display_id>[\w_-]+)?$", views.signage_display, name="signage_display"),

    url(r"^/eighth(?:/(?P<block_id>\d+))?$", views.eighth_signage, name="eighth_signage"),
    url(r"^/schedule$", views.schedule_signage, name="schedule_signage"),
    url(r"^/status$", views.status_signage, name="status_signage"),
]
