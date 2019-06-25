

from django.conf.urls import url
from . import views

urlpatterns = [url(r"^/vote/(?P<username>\w+)/(?P<position>.+)$", views.vote_for_user, name="vote_for_user")]
