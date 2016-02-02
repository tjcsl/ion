# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^/android/setup$", views.android_setup_view, name="notif_android_setup"),
    url(r"^/chrome/setup$", views.chrome_setup_view, name="notif_chrome_setup"),
    url(r"^/chrome/getdata$", views.chrome_getdata_view, name="notif_chrome_getdata"),
    url(r"^/gcm/post$", views.gcm_post_view, name="notif_gcm_post"),
    url(r"^/gcm/list$", views.gcm_list_view, name="notif_gcm_list")
]
