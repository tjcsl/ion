# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
import django.contrib.admin
from django.views.generic.base import RedirectView, TemplateView
from intranet.apps.error.views import handle_404_view, handle_500_view

django.contrib.admin.autodiscover()

urlpatterns = [
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico"), name="favicon"),
    url(r"^robots\.txt$", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots"),
    url(r"^api", include("intranet.apps.api.urls"), name="api_root"),

    url(r"^", include("intranet.apps.auth.urls")),

    url(r"^announcements", include("intranet.apps.announcements.urls")),
    url(r"^eighth", include("intranet.apps.eighth.urls")),
    url(r"^events", include("intranet.apps.events.urls")),
    url(r"^files", include("intranet.apps.files.urls")),
    url(r"^groups", include("intranet.apps.groups.urls")),
    url(r"^polls", include("intranet.apps.polls.urls")),
    url(r"^search", include("intranet.apps.search.urls")),
    url(r"^profile", include("intranet.apps.users.urls")),
    url(r"^schedule", include("intranet.apps.schedule.urls")),
    url(r"^feedback", include("intranet.apps.feedback.urls")),
    url(r"^welcome", include("intranet.apps.welcome.urls")),
    url(r"^notifications", include("intranet.apps.notifications.urls")),
    url(r"^prefs", include("intranet.apps.prefs.urls")),

    url(r"^djangoadmin/", include(django.contrib.admin.site.urls)),
]


if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ]


handler404 = handle_404_view
handler500 = handle_500_view
