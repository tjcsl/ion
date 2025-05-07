from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.preferences_view, name="preferences"),
    re_path(r"^/privacy$", views.privacy_options_view, name="privacy_options"),
    re_path(r"^/verify_email/(?P<email_uuid>[0-9a-fA-F-]{36})$", views.verify_email_view, name="verify_email"),  # The path only accepts valid UUIDs.
]
