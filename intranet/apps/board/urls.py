# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home, name="board_home"),
    url(ur"^/class/(?P<class_id>.*)?$", views.class_feed, name="board_class"),
    url(ur"^/section/(?P<section_id>.*)?$", views.section_feed, name="board_section")

]
