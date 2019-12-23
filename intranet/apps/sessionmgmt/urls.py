from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index_view, name="sessionmgmt"),
    re_path(r"^/trust$", views.trust_session_view, name="trust_session"),
    re_path(r"^/revoke$", views.revoke_session_view, name="revoke_session"),
    re_path(r"^/global-logout$", views.global_logout_view, name="global_logout"),
]
