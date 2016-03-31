# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home, name="board"),
    url(r"^/course/(?P<course_id>.*)?$", views.course_feed, name="board_course"),
    url(r"^/submit/course/(?P<course_id>.*)?$", views.course_feed_post, name="board_course_post"),

    url(r"^/section/(?P<section_id>.*)?$", views.section_feed, name="board_section"),
    url(r"^/submit/section/(?P<section_id>.*)?$", views.section_feed_post, name="board_section_post"),

    url(r"^/post/(?P<post_id>\d+)?$", views.view_post, name="board_post"),

    url(r"^/post/(?P<post_id>\d+)/comment$", views.comment_view, name="board_comment"),

    # url(r"^/add$", views.add_post_view, name="add_boardpost"),
    url(r"^/post/(?P<id>\d+)/modify$", views.modify_post_view, name="board_modify_post"),
    url(r"^/post/(?P<id>\d+)/delete$", views.delete_post_view, name="board_delete_post"),
    url(r"^/comment/(?P<id>\d+)/delete$", views.delete_comment_view, name="board_delete_comment"),

]
