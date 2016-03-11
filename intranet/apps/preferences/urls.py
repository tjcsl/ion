# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.preferences_view, name="preferences"),
    url(r"^/privacy$", views.privacy_options_view, name="privacy_options"),
    url(r"^/ldap_test$", views.ldap_test, name="ldap_test")
]
