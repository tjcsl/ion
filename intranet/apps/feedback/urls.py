# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [url(r"^$", views.send_feedback_view, name="send_feedback"),]
