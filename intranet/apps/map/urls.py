# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.map_view, name="map"),
    url(r"^/first$", views.get_svg_view, {"floor": "first"}, name="map_first_floor"),
    url(r"^/second$", views.get_svg_view, {"floor": "second"}, name="map_second_floor"),
    url(r"^/lookup$", views.room_name_from_id_view, name="room_id_lookup"),
]
