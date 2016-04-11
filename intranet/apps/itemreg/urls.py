# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.home_view, name="itemreg"),

    url(r"^/lostitem/add$", views.lostitem_add_view, name="lostitem_add"),
    url(r"^/lostitem/modify/(?P<item_id>\d+)?$", views.lostitem_modify_view, name="lostitem_modify"),
    url(r"^/lostitem/delete/(?P<item_id>\d+)?$", views.lostitem_delete_view, name="lostitem_delete"),
    url(r"^/lostitem/(?P<item_id>\d+)?$", views.lostitem_view, name="lostitem_view"),

    url(r"^/founditem/add$", views.founditem_add_view, name="founditem_add"),
    url(r"^/founditem/modify/(?P<item_id>\d+)?$", views.founditem_modify_view, name="founditem_modify"),
    url(r"^/founditem/delete/(?P<item_id>\d+)?$", views.founditem_delete_view, name="founditem_delete"),
    url(r"^/founditem/(?P<item_id>\d+)?$", views.founditem_view, name="founditem_view"),
]
