from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.view_announcements, name="view_announcements"),
    re_path(r"^/archive$", views.view_announcements_archive, name="announcements_archive"),
    re_path(r"^/add$", views.add_announcement_view, name="add_announcement"),
    re_path(r"^/request$", views.request_announcement_view, name="request_announcement"),
    re_path(r"^/request/success$", views.request_announcement_success_view, name="request_announcement_success"),
    re_path(r"^/request/success_self$", views.request_announcement_success_self_view, name="request_announcement_success_self"),
    re_path(r"^/approve/(?P<req_id>\d+)$", views.approve_announcement_view, name="approve_announcement"),
    re_path(r"^/approve/success$", views.approve_announcement_success_view, name="approve_announcement_success"),
    re_path(r"^/approve/reject$", views.approve_announcement_reject_view, name="approve_announcement_reject"),
    re_path(r"^/admin_approve/(?P<req_id>\d+)$", views.admin_approve_announcement_view, name="admin_approve_announcement"),
    re_path(r"^/admin_status$", views.admin_request_status_view, name="admin_request_status"),
    re_path(r"^/modify/(?P<announcement_id>\d+)$", views.modify_announcement_view, name="modify_announcement"),
    re_path(r"^/delete/(?P<announcement_id>\d+)$", views.delete_announcement_view, name="delete_announcement"),
    re_path(r"^/show$", views.show_announcement_view, name="show_announcement"),
    re_path(r"^/hide$", views.hide_announcement_view, name="hide_announcement"),
    re_path(r"^/(?P<announcement_id>\d+)$", views.view_announcement_view, name="view_announcement"),
]
