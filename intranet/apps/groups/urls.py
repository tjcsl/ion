from django.urls import re_path

from . import views

urlpatterns = [re_path(r"^$", views.groups_view, name="groups"), re_path(r"^/add$", views.add_group_view, name="add_groups")]
