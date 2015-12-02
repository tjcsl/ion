# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^student$", views.student_welcome_view, name="welcome_student"),
    url(r"^teacher$", views.teacher_welcome_view, name="welcome_teacher"),
    url(r"^done$", views.done_welcome_view, name="welcome_done"),
    url(r"^$", views.welcome_view, name="welcome")
]
