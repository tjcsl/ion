# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
import views

urlpatterns = [
    url(r"^$",  views.index_view, name="index"),
    url(r"^login$", views.login_view.as_view(), name="login"),
    url(r"^logout$", views.logout_view, name="logout"),
]
