# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.parking_intro_view, name="parking"),
    url(r"^/form$", views.parking_form_view, name="parking_form"),
    url(r"^/car$", views.parking_car_view, name="parking_car")

]
