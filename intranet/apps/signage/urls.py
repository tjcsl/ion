# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r"^/display$", views.signage_display, name="signage_display"),
    url(r"^/display/(?P<display_id>[\w_-]+)?$", views.signage_display, name="signage_display"),
]
