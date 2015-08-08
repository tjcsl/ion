# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^$", views.files_view, name="files"),
    url(r"^/(?P<fstype>\w+)$", views.files_type, name="files_type"),
    url(r"^/(?P<fstype>\w+)?dir=(?P<fsdir>\w+)$", views.files_type, name="files_type_dir"),
    
]
