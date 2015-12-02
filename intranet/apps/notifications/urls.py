# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^android/setup$", views.android_setup_view, name="notif_android_setup"),
    url(r"^android/gcm_post$", views.gcm_post_view, name="notif_gcm_post"),
    url(r"^android/gcm_list$", views.gcm_list_view, name="notif_gcm_list")
]
