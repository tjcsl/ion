# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^/android/setup$", views.android_setup_view, name="notif_android_setup_view"),
]
