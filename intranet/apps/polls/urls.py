# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
import views


urlpatterns = [
    url(r"^$", views.polls_view, name="polls"),
]
