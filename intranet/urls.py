from django.conf.urls import patterns, url, include
from django.views.generic.base import TemplateView, RedirectView
from rest_framework import routers
from .apps.auth.views import index, login_view, logout_view
from .apps.users.views import profile_view, picture_view
from .apps.eighth.views import eighth_signup_view
from .apps.events.views import events_view
from .apps.groups.views import groups_view
from .apps.polls.views import polls_view
from .apps.files.views import files_view

urlpatterns = patterns("auth.views.",
    url(r"^$", index),
    url(r"^login$", login_view.as_view()),
    url(r"^logout$", logout_view),
)

urlpatterns += patterns("users.views.",
    url(r"^profile/(?P<user_id>\d+)?$", profile_view),
    url(r"^picture/(?P<user_id>\d+)/(?P<year>freshman|sophomore|junior|senior)?$", picture_view)
)

urlpatterns += patterns("eighth.views.",
    url(r"^eighth/(?P<block_id>\d+)?$", eighth_signup_view),
)

urlpatterns += patterns("events.views.",
    url(r"^events$", events_view),
)

urlpatterns += patterns("groups.views.",
                        url(r"^groups$", groups_view),
                        )

urlpatterns += patterns("polls.views.",
    url(r"^polls$", polls_view),
)

urlpatterns += patterns("files.views.",
    url(r"^files$", files_view),
)

urlpatterns += patterns("",
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico")),
    # url(r"^\(productivity\)/cpuspam/botspam$", TemplateView.as_view(template_name="cpuspam.html"))
    url(r"^api/", include("intranet.apps.api.urls")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
)

