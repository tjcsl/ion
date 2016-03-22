# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home, name="board"),
    url(r"^/class/(?P<class_id>.*)?$", views.class_feed, name="board_class"),
    url(r"^/post/class/(?P<class_id>.*)?$", views.class_feed_post, name="board_class_post"),

    url(r"^/section/(?P<section_id>.*)?$", views.section_feed, name="board_section"),
    url(r"^/post/section/(?P<section_id>.*)?$", views.section_feed_post, name="board_section_post"),

    url(r"^/comment/(?P<post_id>\d+)$", views.comment_view, name="board_comment"),

    # url(r"^/add$", views.add_post_view, name="add_boardpost"),
    url(r"^/modify/(?P<id>\d+)$", views.modify_post_view, name="modify_boardpost"),

]
