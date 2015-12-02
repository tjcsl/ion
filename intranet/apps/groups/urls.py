# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^$", views.groups_view, name="groups"),
    url(r"^/add$", views.add_group_view, name="add_groups")
]
