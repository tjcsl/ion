# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from intranet.apps.oauth.views import ApplicationUpdateView
from intranet.apps.error.views import (handle_404_view, handle_500_view, handle_503_view)

admin.autodiscover()

admin.site.site_header = "Ion administration"  # type: ignore

urlpatterns = [
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico"), name="favicon"),
    url(r"^robots\.txt$", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots"),
    url(r"^manifest\.json$", RedirectView.as_view(url="/static/manifest.json"), name="chrome_manifest"),
    url(r"^serviceworker\.js$", TemplateView.as_view(template_name="serviceworker.js", content_type="text/javascript"), name="chrome_serviceworker"),
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
    url(r"^seniors", include("intranet.apps.seniors.urls")),
    url(r"^preferences", include("intranet.apps.preferences.urls")),
    url(r"^feedback", include("intranet.apps.feedback.urls")),
    url(r"^welcome", include("intranet.apps.welcome.urls")),
    url(r"^notifications", include("intranet.apps.notifications.urls")),
    url(r"^signage", include("intranet.apps.signage.urls")),
    url(r"^printing", include("intranet.apps.printing.urls")),
    url(r"^bus", include("intranet.apps.bus.urls")),
    url(r"^itemreg", include("intranet.apps.itemreg.urls")),
    url(r"^lostfound", include("intranet.apps.lostfound.urls")),
    url(r"^emailfwd", include("intranet.apps.emailfwd.urls")),
    url(r"^parking", include("intranet.apps.parking.urls")),
    url(r"^djangoadmin/doc/", include('django.contrib.admindocs.urls')),
    # FIXME: update when admin supports django 1.10+ properly
    url(r"^djangoadmin/", admin.site.urls),
    url(r"^oauth/applications/(?P<pk>\d+)/update/$", ApplicationUpdateView.as_view()),
    url(r"^oauth/", include(("oauth2_provider.urls", "oauth2_provider"))),
    url(r"^oauth/$", RedirectView.as_view(url="/oauth/applications/"), name="oauth_redirect"),
    url(r"^nominations", include("intranet.apps.nomination.urls")),
    url(r"^courses", include("intranet.apps.users.class_urls")),
    url(r"^prometheus/", include('django_prometheus.urls')),
]

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [url(r"^__debug__/", include(debug_toolbar.urls))]  # type: ignore

handler404 = handle_404_view
handler500 = handle_500_view
handler503 = handle_503_view  # maintenance mode
