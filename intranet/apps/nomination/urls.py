from django.urls import re_path

from . import views

urlpatterns = [re_path(r"^/vote/(?P<username>\w+)/(?P<position>.+)$", views.vote_for_user, name="vote_for_user")]
