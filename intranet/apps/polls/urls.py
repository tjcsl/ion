# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^$", views.polls_view, name="polls"),
    url(r"^add$", views.add_poll_view, name="add_poll"),
    url(r"^modify/(?P<id>\d+)$", views.modify_poll_view, name="modify_poll"),
    url(r"^delete/(?P<id>\d+)$", views.modify_poll_view, name="delete_poll"),
]
