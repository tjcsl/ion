# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.events_view, name="events"),
    url(r"^/add$", views.add_event_view, name="add_event"),
    url(r"^/request$", views.request_event_view, name="request_event"),
    url(r"^/modify/(?P<event_id>\d+)$", views.modify_event_view, name="modify_event"),
    url(r"^/delete/(?P<event_id>\d+)$", views.delete_event_view, name="delete_event"),
    url(r"^/join/(?P<event_id>\d+)$", views.join_event_view, name="join_event"),
    url(r"^/roster/(?P<event_id>\d+)$", views.event_roster_view, name="event_roster"),
    url(r"^/show$", views.show_event_view, name="show_event"),
    url(r"^/hide$", views.hide_event_view, name="hide_event"),
    url(r"^/(?P<event_id>\d+)$", views.event_roster_view, name="event"),
]
