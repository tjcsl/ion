from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^(?:/(?P<user_id>\d+))?$", views.profile_view, name="user_profile"),
    re_path(r"^/picture/(?P<user_id>\d+)(?:/(?P<year>freshman|sophomore|junior|senior))?$", views.picture_view, name="profile_picture"),
]
