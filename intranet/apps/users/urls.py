# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^(?:/(?P<user_id>\d+))?$", views.profile_view, name="user_profile"),
    url(r"^/picture/(?P<user_id>\d+)(?:/(?P<year>freshman|sophomore|junior|senior))?$", views.picture_view, name="profile_picture"),
    url(r"^/class/(?P<section_id>.*)?$", views.class_section_view, name="class_section"),
    url(r"^/class_csv/(?P<section_id>.*)?$", views.class_section_view, name="class_section_csv"),
    url(r"^/room/(?P<room_id>.*)?$", views.class_room_view, name="class_room"), url(r"^/all_classes/?$", views.all_classes_view, name="all_classes")
]
