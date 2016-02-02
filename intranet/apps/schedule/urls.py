# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    # Admin
    url(r"^$", views.admin_home_view, name="schedule_admin"),
    url(r"^/view$", views.schedule_view, name="schedule"),
    url(r"^/embed$", views.schedule_embed, name="schedule_embed"),
    url(r"^/widget$", views.schedule_widget_view, name="schedule_widget"),
    url(r"^/daytype(?:/(?P<id>\d+))?$", views.admin_daytype_view, name="schedule_daytype"),
    url(r"^/add$", views.admin_add_view, name="schedule_add"),
    url(r"^/comment$", views.admin_comment_view, name="schedule_comment"),

]
