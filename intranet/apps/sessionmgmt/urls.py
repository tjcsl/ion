from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_view, name="sessionmgmt"),
    path("/trust", views.trust_session_view, name="trust_session"),
    path("/revoke", views.revoke_session_view, name="revoke_session"),
    path("/global-logout", views.global_logout_view, name="global_logout"),
]
