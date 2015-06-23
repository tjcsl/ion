# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^$", views.events_view, name="events"),
    url(r"^/add$", views.events_add_view, name="events_add"),
]
