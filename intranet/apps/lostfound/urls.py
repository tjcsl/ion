from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.home_view, name="lostfound"),
    re_path(r"^/lost/add$", views.lostitem_add_view, name="lostitem_add"),
    re_path(r"^/lost/modify/(?P<item_id>\d+)?$", views.lostitem_modify_view, name="lostitem_modify"),
    re_path(r"^/lost/delete/(?P<item_id>\d+)?$", views.lostitem_delete_view, name="lostitem_delete"),
    re_path(r"^/lost/(?P<item_id>\d+)?$", views.lostitem_view, name="lostitem_view"),
    re_path(r"^/found/add$", views.founditem_add_view, name="founditem_add"),
    re_path(r"^/found/modify/(?P<item_id>\d+)?$", views.founditem_modify_view, name="founditem_modify"),
    re_path(r"^/found/delete/(?P<item_id>\d+)?$", views.founditem_delete_view, name="founditem_delete"),
    re_path(r"^/found/(?P<item_id>\d+)?$", views.founditem_view, name="founditem_view"),
]
