# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^/senior$", views.senior_email_forward_view, name="senior_emailfwd"),

]
