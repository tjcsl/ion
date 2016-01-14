# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.files_view, name="files"),
    url(r"^/auth$", views.files_auth, name="files_auth"),
    url(r"^/(?P<fstype>\w+)$", views.files_type, name="files_type"),
    url(r"^/(?P<fstype>\w+)/upload$", views.files_upload, name="files_upload"),
    url(r"^/(?P<fstype>\w+)?dir=(?P<fsdir>\w+)$", views.files_type, name="files_type_dir"),

]
