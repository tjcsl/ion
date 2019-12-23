from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.events_view, name="events"),
    re_path(r"^/add$", views.add_event_view, name="add_event"),
    re_path(r"^/request$", views.request_event_view, name="request_event"),
    re_path(r"^/modify/(?P<event_id>\d+)$", views.modify_event_view, name="modify_event"),
    re_path(r"^/delete/(?P<event_id>\d+)$", views.delete_event_view, name="delete_event"),
    re_path(r"^/join/(?P<event_id>\d+)$", views.join_event_view, name="join_event"),
    re_path(r"^/roster/(?P<event_id>\d+)$", views.event_roster_view, name="event_roster"),
    re_path(r"^/show$", views.show_event_view, name="show_event"),
    re_path(r"^/hide$", views.hide_event_view, name="hide_event"),
    re_path(r"^/(?P<event_id>\d+)$", views.event_roster_view, name="event"),
]
