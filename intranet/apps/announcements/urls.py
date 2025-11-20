from django.urls import path

from . import views

urlpatterns = [
    path("", views.view_announcements, name="view_announcements"),
    path("/archive", views.view_announcements_archive, name="announcements_archive"),
    path("/club", views.view_club_announcements, name="club_announcements"),
    path("/add", views.add_announcement_view, name="add_announcement"),
    path("/request", views.request_announcement_view, name="request_announcement"),
    path("/club/add", views.add_club_announcement_view, name="add_club_announcement"),
    path("/club/modify/<int:announcement_id>", views.modify_club_announcement_view, name="modify_club_announcement"),
    path("/request/success", views.request_announcement_success_view, name="request_announcement_success"),
    path("/request/success_self", views.request_announcement_success_self_view, name="request_announcement_success_self"),
    path("/approve/<int:req_id>", views.approve_announcement_view, name="approve_announcement"),
    path("/approve/success", views.approve_announcement_success_view, name="approve_announcement_success"),
    path("/approve/reject", views.approve_announcement_reject_view, name="approve_announcement_reject"),
    path("/admin_approve/<int:req_id>", views.admin_approve_announcement_view, name="admin_approve_announcement"),
    path("/admin_status", views.admin_request_status_view, name="admin_request_status"),
    path("/modify/<int:announcement_id>", views.modify_announcement_view, name="modify_announcement"),
    path("/delete/<int:announcement_id>", views.delete_announcement_view, name="delete_announcement"),
    path("/show", views.show_announcement_view, name="show_announcement"),
    path("/hide", views.hide_announcement_view, name="hide_announcement"),
    path("/<int:announcement_id>", views.view_announcement_view, name="view_announcement"),
]
