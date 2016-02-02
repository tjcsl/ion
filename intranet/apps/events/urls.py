# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.events_view, name="events"),
    url(r"^/add$", views.add_event_view, name="add_event"),
    url(r"^/modify/(?P<id>\d+)$", views.modify_event_view, name="modify_event"),
    url(r"^/delete/(?P<id>\d+)$", views.delete_event_view, name="delete_event"),
    url(r"^/join/(?P<id>\d+)$", views.join_event_view, name="join_event"),
    url(r"^/roster/(?P<id>\d+)$", views.event_roster_view, name="event_roster"),
    url(r"^/(?P<id>\d+)$", views.event_roster_view, name="event"),
]
