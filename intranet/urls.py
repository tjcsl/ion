from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.urls import include, re_path
from django.views.generic.base import RedirectView, TemplateView

from intranet.apps.error.views import handle_404_view, handle_500_view, handle_503_view
from intranet.apps.oauth.views import ApplicationDeleteView, ApplicationRegistrationView, ApplicationUpdateView

admin.autodiscover()

admin.site.site_header = "Ion Administration"  # type: ignore

urlpatterns = [
    re_path(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon/favicon.ico"), name="favicon"),
    re_path(r"^robots\.txt$", RedirectView.as_view(url="/static/robots.txt"), name="robots"),
    re_path(r"^manifest\.json$", RedirectView.as_view(url="/static/manifest.json"), name="chrome_manifest"),
    re_path(r"^serviceworker\.js$", RedirectView.as_view(url="/static/serviceworker.js"), name="chrome_serviceworker"),
    path("api", include("intranet.apps.api.urls"), name="api_root"),
    path("", include("intranet.apps.auth.urls")),
    path("announcements", include("intranet.apps.announcements.urls")),
    path("apps", include("intranet.apps.cslapps.urls")),
    path("eighth", include("intranet.apps.eighth.urls")),
    path("enrichment", include("intranet.apps.enrichment.urls")),
    path("events", include("intranet.apps.events.urls")),
    path("files", include("intranet.apps.files.urls")),
    path("groups", include("intranet.apps.groups.urls")),
    path("polls", include("intranet.apps.polls.urls")),
    path("search", include("intranet.apps.search.urls")),
    path("profile", include("intranet.apps.users.urls")),
    path("schedule", include("intranet.apps.schedule.urls")),
    path("seniors", include("intranet.apps.seniors.urls")),
    path("preferences", include("intranet.apps.preferences.urls")),
    path("feedback", include("intranet.apps.feedback.urls")),
    path("welcome", include("intranet.apps.welcome.urls")),
    path("notifications", include("intranet.apps.notifications.urls")),
    path("signage", include("intranet.apps.signage.urls")),
    path("printing", include("intranet.apps.printing.urls")),
    path("bus", include("intranet.apps.bus.urls")),
    path("itemreg", include("intranet.apps.itemreg.urls")),
    path("lostfound", include("intranet.apps.lostfound.urls")),
    path("emailfwd", include("intranet.apps.emailfwd.urls")),
    path("parking", include("intranet.apps.parking.urls")),
    path("sessions", include("intranet.apps.sessionmgmt.urls")),
    path("themes", include("intranet.apps.customthemes.urls")),
    path("logs", include("intranet.apps.logs.urls")),
    path("djangoadmin/doc/", include("django.contrib.admindocs.urls")),
    # FIXME: update when admin supports django 1.10+ properly
    re_path(r"^djangoadmin/", admin.site.urls),
    path("oauth/applications/<int:pk>/update/", ApplicationUpdateView.as_view()),
    path("oauth/applications/<int:pk>/delete/", ApplicationDeleteView.as_view()),
    path("oauth/applications/register/", ApplicationRegistrationView.as_view()),
    path("oauth/", include(("oauth2_provider.urls", "oauth2_provider"))),
    path("oauth/", RedirectView.as_view(url="/oauth/applications/"), name="oauth_redirect"),
    path("nominations", include("intranet.apps.nomination.urls")),
    path("courses", include("intranet.apps.users.courses_urls")),
    path("features", include("intranet.apps.features.urls", namespace="features")),
    path("prometheus/", include("django_prometheus.urls")),
    path("docs/accounts", TemplateView.as_view(template_name="docs/accounts.html", content_type="text/html"), name="docs_accounts"),
    path(
        "docs/api-oauth-aup", TemplateView.as_view(template_name="docs/api-oauth-aup.html", content_type="text/html"), name="docs_api_oauth_aup"
    ),
    path("docs/terminology", TemplateView.as_view(template_name="docs/terminology.html", content_type="text/html"), name="docs_terminology"),
    path("docs/privacy", TemplateView.as_view(template_name="docs/privacy.html", content_type="text/html"), name="docs_privacy"),
    path(
        "docs/add-to-home-screen-android",
        TemplateView.as_view(template_name="docs/add-to-home-screen-android.html", content_type="text/html"),
        name="docs_add_to_home_screen_android",
    ),
]

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]  # type: ignore

handler404 = handle_404_view
handler500 = handle_500_view
handler503 = handle_503_view  # maintenance mode
