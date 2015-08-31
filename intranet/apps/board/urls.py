# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home, name="board_home"),
    url(ur"^/class/(?P<class_id>.*)?$", views.class_feed, name="board_class"),
    url(ur"^/post/class/(?P<class_id>.*)?$", views.class_feed_post, name="board_class_post"),

    url(ur"^/section/(?P<section_id>.*)?$", views.section_feed, name="board_section"),
    #url(ur"^/section/(?P<section_id>.*)?/add$", views.section_feed_add, name="board_section_add"),

    #url(r"^/add$", views.add_post_view, name="add_boardpost"),
    url(r"^/modify/(?P<id>\d+)$", views.modify_post_view, name="modify_boardpost"),

]
