# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^/android/setup$", views.android_setup_view, name="notif_android_setup"),
    url(r"^/chrome/setup$", views.chrome_setup_view, name="notif_chrome_setup"),
    url(r"^/gcm/android/post$", views.gcm_android_post_view, name="notif_gcm_android_post"),
    url(r"^/gcm/chrome/post$", views.gcm_chrome_post_view, name="notif_gcm_chrome_post"),
    url(r"^/gcm/list$", views.gcm_list_view, name="notif_gcm_list")
]
