from django.conf.urls import patterns, url, include
from django.views.generic.base import TemplateView, RedirectView
from rest_framework import routers
from .apps.auth.views import index, login_view, logout_view
from .apps.users.views import profile_view, picture_view
from .apps.eighth.views import eighth_signup_view
from .apps.events.views import events_view
from .apps.groups.views import groups_view, add_group_view
from .apps.polls.views import polls_view
from .apps.files.views import files_view
from .apps.announcements.views import add_announcement_view, modify_announcement_view, delete_announcement_view
#from .apps.admin.views import admin_view, admin_eighth_view

urlpatterns = patterns("",
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico"), name="favicon"),
    # url(r"^\(productivity\)/cpuspam/botspam$", TemplateView.as_view(template_name="cpuspam.html"))
    url(r"^api/", include("intranet.apps.api.urls"), name="api_root"),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
)

urlpatterns += patterns("auth.views.",
    url(r"^$", index, name="index"),
    url(r"^login$", login_view.as_view(), name="login"),
    url(r"^logout$", logout_view, name="logout"),
)

urlpatterns += patterns("announcements.views.",
    url(r"^announcements/add$", add_announcement_view, name="add_announcement"),
    url(r"^announcements/modify/(?P<id>\d+)$", modify_announcement_view, name="modify_announcement"),
    url(r"^announcements/delete$", delete_announcement_view, name="delete_announcement"),
)

urlpatterns += patterns("eighth.views.",
    url(r"^eighth(?:/(?P<block_id>\d+))?$", eighth_signup_view, name="eighth"),
)

urlpatterns += patterns("events.views.",
    url(r"^events$", events_view, name="events"),
)

urlpatterns += patterns("files.views.",
    url(r"^files$", files_view, name="files"),
)

urlpatterns += patterns("groups.views.",
    url(r"^groups$", groups_view, name="groups"),
	url(r"^groups/add$", add_group_view, name="add_groups"),
)

urlpatterns += patterns("polls.views.",
    url(r"^polls$", polls_view, name="polls"),
)

#urlpatterns += patterns("admin.views.",
#    url(r"^admin$", admin_view, name="admin"),
#    url(r"^admin/eighth$", admin_eighth_view, name="admin_eighth")
#)

urlpatterns += patterns("users.views.",
    url(r"^profile(?:/(?P<user_id>\d+))?$", profile_view, name="user_profile"),
    url(r"^picture/(?P<user_id>\d+)(?:/(?P<year>freshman|sophomore|junior|senior))?$", picture_view, name="profile_picture")
)
