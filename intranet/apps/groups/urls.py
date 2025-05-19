from django.urls import path

from . import views

urlpatterns = [path("", views.groups_view, name="groups"), path("/add", views.add_group_view, name="add_groups")]
