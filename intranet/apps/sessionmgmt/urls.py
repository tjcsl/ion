from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.index_view, name="sessionmgmt"),
    url(r"^/trust$", views.trust_session_view, name="trust_session"),
    url(r"^/revoke$", views.revoke_session_view, name="revoke_session"),
    url(r"^/global-logout$", views.global_logout_view, name="global_logout"),
]
