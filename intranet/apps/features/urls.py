from django.urls import re_path

from . import views

app_name = "features"

urlpatterns = [
    re_path(r"^/dismiss-announcement/(?P<feat_announcement_id>\d+)$", views.dismiss_feat_announcement_view, name="dismiss_feat_announcement")
]
