from django.conf import settings
from django.urls import path

from . import views

urlpatterns = []

if settings.ENABLE_ENRICHMENT_APP:
    urlpatterns = [
        path("", views.enrichment_view, name="enrichment"),
        path("/add", views.add_enrichment_view, name="add_enrichment"),
        path("/modify/<int:enrichment_id>", views.modify_enrichment_view, name="modify_enrichment"),
        path("/delete/<int:enrichment_id>", views.delete_enrichment_view, name="delete_enrichment"),
        path("/join/<int:enrichment_id>", views.enrichment_signup_view, name="enrichment_signup"),
        path("/roster/<int:enrichment_id>", views.enrichment_roster_view, name="enrichment_roster"),
        path("/<int:enrichment_id>", views.enrichment_roster_view, name="enrichment"),
    ]
