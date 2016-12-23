# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^/iframe$", views.get_iframe_content_view, name="map_iframe"),
    url(r"^/lookup$", views.room_name_from_id_view, name="room_id_lookup"),
]
