# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.polls_view, name="polls"),
    url(r"^/vote/(?P<poll_id>\d+)$", views.poll_vote_view, name="poll_vote"),
    url(r"^/results/(?P<poll_id>\d+)$", views.poll_results_view, name="poll_results"),


    url(r"^/add$", views.add_poll_view, name="add_poll"),
    url(r"^/modify/(?P<poll_id>\d+)$", views.modify_poll_view, name="modify_poll"),
    url(r"^/delete/(?P<poll_id>\d+)$", views.modify_poll_view, name="delete_poll"),
]
