# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^/eighth(?:/(?P<block_id>\d+))?$", views.eighth_signage, name="eighth_signage"),
    url(r"^/display/(?P<display_id>[\w_-]+)?$", views.signage_display, name="signage_display"),
]
