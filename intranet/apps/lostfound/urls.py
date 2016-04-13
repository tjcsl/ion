# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home_view, name="lostfound"),

    url(r"^/lost/add$", views.lostitem_add_view, name="lostitem_add"),
    url(r"^/lost/modify/(?P<item_id>\d+)?$", views.lostitem_modify_view, name="lostitem_modify"),
    url(r"^/lost/delete/(?P<item_id>\d+)?$", views.lostitem_delete_view, name="lostitem_delete"),
    url(r"^/lost/(?P<item_id>\d+)?$", views.lostitem_view, name="lostitem_view"),

    url(r"^/found/add$", views.founditem_add_view, name="founditem_add"),
    url(r"^/found/modify/(?P<item_id>\d+)?$", views.founditem_modify_view, name="founditem_modify"),
    url(r"^/found/delete/(?P<item_id>\d+)?$", views.founditem_delete_view, name="founditem_delete"),
    url(r"^/found/(?P<item_id>\d+)?$", views.founditem_view, name="founditem_view"),
]
