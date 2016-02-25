# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.main_view, name="ionldap_main"),
    url(r"^/class/(?P<section_id>.*)?$", views.class_section_view, name="ionldap_class_section"),
    url(r"^/class_csv/(?P<section_id>.*)?$", views.class_section_view, name="ionldap_class_section_csv"),
    url(r"^/room/(?P<room_id>.*)?$", views.class_room_view, name="ionldap_class_room"),
    url(r"^/all_classes/?$", views.all_classes_view, name="ionldap_all_classes")

]
