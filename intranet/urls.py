from django.conf import settings
from django.conf.urls import patterns, url, include
import django.contrib.admin
from django.views.generic.base import RedirectView
from .apps.auth.views import login_view

django.contrib.admin.autodiscover()

urlpatterns = patterns(
    "",
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico"), name="favicon"),
    # url(r"^api/", include("intranet.apps.api.urls"), name="api_root"),
    # url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
)

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns += patterns(
        "",
        url(r"^__debug__/", include(debug_toolbar.urls)),
    )


urlpatterns += patterns(
    "intranet.apps.auth.views",
    url(r"^$",                                          "index_view",                               name="index"),
    url(r"^login$",                                     login_view.as_view(),                       name="login"),
    url(r"^logout$",                                    "logout_view",                              name="logout"),
)

urlpatterns += patterns(
    "intranet.apps.announcements.views",
    url(r"^announcements/add$",                         "add_announcement_view",                    name="add_announcement"),
    url(r"^announcements/modify/(?P<id>\d+)$",          "modify_announcement_view",                 name="modify_announcement"),
    url(r"^announcements/delete$",                      "delete_announcement_view",                 name="delete_announcement"),
)

urlpatterns += patterns(
    "intranet.apps.eighth.views",
    url(r"^eighth$",                                    "routers.eighth_redirect_view",             name="eighth_redirect"),
    # url(r"^eighth/admin$",                              "admin.navigation.admin_index_view",        name="eighth_admin"),
    # url(r"^eighth/attendance$",                         "admin.attendance.attendance_view",         name="eighth_attendance"),
    url(r"^eighth/signup(?:/(?P<block_id>\d+))?$",      "students.eighth_signup_view",              name="eighth_signup"),
)

urlpatterns += patterns(
    "intranet.apps.events.views",
    url(r"^events$", "events_view", name="events"),
)

urlpatterns += patterns(
    "intranet.apps.files.views",
    url(r"^files$", "files_view", name="files"),
)

urlpatterns += patterns(
    "intranet.apps.groups.views",
    url(r"^groups$",        "groups_view",      name="groups"),
    url(r"^groups/add$",    "add_group_view",   name="add_groups"),
)

urlpatterns += patterns(
    "intranet.apps.polls.views",
    url(r"^polls$", "polls_view", name="polls"),
)

urlpatterns += patterns(
    "intranet.apps.users.views",
    url(r"^profile(?:/(?P<user_id>\d+))?$",                                                 "profile_view", name="user_profile"),
    url(r"^picture/(?P<user_id>\d+)(?:/(?P<year>freshman|sophomore|junior|senior))?$",      "picture_view", name="profile_picture")
)

urlpatterns += patterns(
    "intranet.apps.search.views",
    url(r"^search$", "search_view", name="search"),
)

urlpatterns += patterns(
    "",
    url(r'^djangoadmin/', include(django.contrib.admin.site.urls)),
)
