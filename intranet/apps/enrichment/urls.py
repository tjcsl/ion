from django.conf import settings
from django.urls import re_path

from . import views

urlpatterns = []

if settings.ENABLE_ENRICHMENT_APP:
    urlpatterns = [
        re_path(r"^$", views.enrichment_view, name="enrichment"),
        re_path(r"^/add$", views.add_enrichment_view, name="add_enrichment"),
        re_path(r"^/modify/(?P<enrichment_id>\d+)$", views.modify_enrichment_view, name="modify_enrichment"),
        re_path(r"^/delete/(?P<enrichment_id>\d+)$", views.delete_enrichment_view, name="delete_enrichment"),
        re_path(r"^/join/(?P<enrichment_id>\d+)$", views.enrichment_signup_view, name="enrichment_signup"),
        re_path(r"^/roster/(?P<enrichment_id>\d+)$", views.enrichment_roster_view, name="enrichment_roster"),
        re_path(r"^/(?P<enrichment_id>\d+)$", views.enrichment_roster_view, name="enrichment"),
    ]
