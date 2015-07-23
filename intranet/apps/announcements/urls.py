# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^/add$", views.add_announcement_view, name="add_announcement"),
    url(r"^/request$", views.request_announcement_view, name="request_announcement"),
    url(r"^/approve/(?P<req_id>\d+)$", views.approve_announcement_view, name="approve_announcement"),
    url(r"^/admin_approve/(?P<req_id>\d+)$", views.admin_approve_announcement_view, name="admin_approve_announcement"),
    url(r"^/modify/(?P<id>\d+)$", views.modify_announcement_view, name="modify_announcement"),
    url(r"^/delete/(?P<id>\d+)$", views.delete_announcement_view, name="delete_announcement"),
    url(r"^/show$", views.show_announcement_view, name="show_announcement"),
    url(r"^/hide$", views.hide_announcement_view, name="hide_announcement"),
    url(r"^/(?P<id>\d+)$", views.view_announcement_view, name="view_announcement"),
]
