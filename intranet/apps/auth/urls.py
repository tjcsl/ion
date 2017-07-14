# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.index_view, name="index"),
    url(r"^login$", views.LoginView.as_view(), name="login"),
    url(r"^logout$", views.logout_view, name="logout"),
    url(r"^about$", views.about_view, name="about"),
    url(r"^reauthenticate$", views.reauthentication_view, name="reauth"),
    url(r"^reset_password$", views.reset_password_view, name="reset_password"),
]
