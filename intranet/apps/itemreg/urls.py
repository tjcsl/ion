# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home_view, name="itemreg"),

    url(r"^/search$", views.search_view, name="itemreg_search"),

    url(r"^/register/calculator$", views.register_calculator_view, name="itemreg_calculator"),
    url(r"^/register/computer$", views.register_computer_view, name="itemreg_computer"),
    url(r"^/register/phone$", views.register_phone_view, name="itemreg_phone"),

    url(r"^/delete/(?P<type>\w+)/(?P<id>\d+)?$", views.register_delete_view, name="itemreg_delete"),
]
