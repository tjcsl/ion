from django.urls import path

from . import views

urlpatterns = [
    path("", views.events_view, name="events"),
    path("/add", views.add_event_view, name="add_event"),
    path("/request", views.request_event_view, name="request_event"),
    path("/modify/<int:event_id>", views.modify_event_view, name="modify_event"),
    path("/delete/<int:event_id>", views.delete_event_view, name="delete_event"),
    path("/join/<int:event_id>", views.join_event_view, name="join_event"),
    path("/roster/<int:event_id>", views.event_roster_view, name="event_roster"),
    path("/show", views.show_event_view, name="show_event"),
    path("/hide", views.hide_event_view, name="hide_event"),
    path("/<int:event_id>", views.event_roster_view, name="event"),
]
