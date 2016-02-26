# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [url(r"^$", views.seniors_home_view, name="seniors"), url(r"^/add$", views.seniors_add_view, name="seniors_add")]
