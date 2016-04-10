# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home_view, name="itemreg"),

    url(r"^/lostitem/add$", views.lostitem_add_view, name="lostitem_add"),
    url(r"^/lostitem/delete/(?P<item_id>\d+)?$", views.lostitem_delete_view, name="lostitem_delete"),

    url(r"^/founditem/add$", views.founditem_add_view, name="founditem_add"),
    url(r"^/founditem/delete/(?P<item_id>\d+)?$", views.founditem_delete_view, name="founditem_delete"),
]
