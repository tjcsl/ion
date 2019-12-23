from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path
from django.views.generic.base import RedirectView, TemplateView

from intranet.apps.error.views import handle_404_view, handle_500_view, handle_503_view
from intranet.apps.oauth.views import ApplicationUpdateView

admin.autodiscover()

admin.site.site_header = "Ion administration"  # type: ignore

urlpatterns = [
    re_path(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico"), name="favicon"),
    re_path(r"^robots\.txt$", RedirectView.as_view(url="/static/robots.txt"), name="robots"),
    re_path(r"^manifest\.json$", RedirectView.as_view(url="/static/manifest.json"), name="chrome_manifest"),
    re_path(r"^serviceworker\.js$", RedirectView.as_view(url="/static/serviceworker.js"), name="chrome_serviceworker"),
    re_path(r"^api", include("intranet.apps.api.urls"), name="api_root"),
    re_path(r"^", include("intranet.apps.auth.urls")),
    re_path(r"^announcements", include("intranet.apps.announcements.urls")),
    re_path(r"^eighth", include("intranet.apps.eighth.urls")),
    re_path(r"^events", include("intranet.apps.events.urls")),
    re_path(r"^files", include("intranet.apps.files.urls")),
    re_path(r"^groups", include("intranet.apps.groups.urls")),
    re_path(r"^polls", include("intranet.apps.polls.urls")),
    re_path(r"^search", include("intranet.apps.search.urls")),
    re_path(r"^profile", include("intranet.apps.users.urls")),
    re_path(r"^schedule", include("intranet.apps.schedule.urls")),
    re_path(r"^seniors", include("intranet.apps.seniors.urls")),
    re_path(r"^preferences", include("intranet.apps.preferences.urls")),
    re_path(r"^feedback", include("intranet.apps.feedback.urls")),
    re_path(r"^welcome", include("intranet.apps.welcome.urls")),
    re_path(r"^notifications", include("intranet.apps.notifications.urls")),
    re_path(r"^signage", include("intranet.apps.signage.urls")),
    re_path(r"^printing", include("intranet.apps.printing.urls")),
    re_path(r"^bus", include("intranet.apps.bus.urls")),
    re_path(r"^itemreg", include("intranet.apps.itemreg.urls")),
    re_path(r"^lostfound", include("intranet.apps.lostfound.urls")),
    re_path(r"^emailfwd", include("intranet.apps.emailfwd.urls")),
    re_path(r"^parking", include("intranet.apps.parking.urls")),
    re_path(r"^sessions", include("intranet.apps.sessionmgmt.urls")),
    re_path(r"^djangoadmin/doc/", include("django.contrib.admindocs.urls")),
    # FIXME: update when admin supports django 1.10+ properly
    re_path(r"^djangoadmin/", admin.site.urls),
    re_path(r"^oauth/applications/(?P<pk>\d+)/update/$", ApplicationUpdateView.as_view()),
    re_path(r"^oauth/", include(("oauth2_provider.urls", "oauth2_provider"))),
    re_path(r"^oauth/$", RedirectView.as_view(url="/oauth/applications/"), name="oauth_redirect"),
    re_path(r"^nominations", include("intranet.apps.nomination.urls")),
    re_path(r"^courses", include("intranet.apps.users.courses_urls")),
    re_path(r"^features", include("intranet.apps.features.urls", namespace="features")),
    re_path(r"^prometheus/", include("django_prometheus.urls")),
    re_path(r"^docs/accounts$", TemplateView.as_view(template_name="docs/accounts.html", content_type="text/html"), name="docs_accounts"),
    re_path(r"^docs/terminology$", TemplateView.as_view(template_name="docs/terminology.html", content_type="text/html"), name="docs_terminology"),
    re_path(r"^docs/privacy$", TemplateView.as_view(template_name="docs/privacy.html", content_type="text/html"), name="docs_privacy"),
]

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [re_path(r"^__debug__/", include(debug_toolbar.urls))]  # type: ignore

handler404 = handle_404_view
handler500 = handle_500_view
handler503 = handle_503_view  # maintenance mode
