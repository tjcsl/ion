# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
import views

urlpatterns = [
    url(r"^add$", views.add_announcement_view, name="add_announcement"),
    url(r"^modify/(?P<id>\d+)$", views.modify_announcement_view, name="modify_announcement"),
    url(r"^delete$", views.delete_announcement_view, name="delete_announcement"),
]
