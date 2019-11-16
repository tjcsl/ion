import binascii
import datetime
import logging
import os
import re

from oauth2_provider.models import Application

from django.conf import settings
from django.urls import Resolver404, resolve
from django.utils import timezone

from intranet.apps.notifications.models import NotificationConfig

from ..utils.helpers import dark_mode_enabled
from .schedule.models import Day

logger = logging.getLogger(__name__)


def ion_base_url(request):
    """
    Return the base URL through request.build_absolute_uri for the index page.
    """
    return {"ion_base_url": request.build_absolute_uri("/")}


def global_warning(request):
    """
    Display a global warning on all pages throughout the application.
    """
    warning = settings.GLOBAL_WARNING if hasattr(settings, "GLOBAL_WARNING") else None

    return {"global_warning": warning}


def nav_categorizer(request):
    """
    Determine which top-level nav category a request falls under
    for the purposes of the left nav bar.
    """

    categories = [
        (r"^/$", "dashboard"),
        (r"^/announcements", "dashboard"),
        (r"^/eighth/admin", "eighth_admin"),
        (r"^/eighth", "eighth"),
        (r"^/events", "events"),
        (r"^/files", "files"),
        (r"^/printing", "printing"),
        (r"^/groups", "groups"),
        (r"^/polls", "polls"),
        (r"^/board", "board"),
        (r"/bus", "bus"),
    ]

    for pattern, category in categories:
        p = re.compile(pattern)
        if p.match(request.path):
            return {"nav_category": category}

    return {"nav_category": ""}


def mobile_app(request):
    """
    Determine if the site is being displayed in a WebView from a native application.
    """

    ctx = {}
    try:
        ua = request.META.get("HTTP_USER_AGENT", "")

        if "IonAndroid: gcmFrame" in ua:
            ctx["is_android_client"] = True
            registered = "appRegistered:False" in ua
            ctx["android_client_registered"] = registered

            if request.user and request.user.is_authenticated:
                """Add/update NotificationConfig object."""

                ncfg, _ = NotificationConfig.objects.get_or_create(user=request.user)
                if not ncfg.android_gcm_rand:
                    rand = binascii.b2a_hex(os.urandom(32))
                    ncfg.android_gcm_rand = rand
                else:
                    rand = ncfg.android_gcm_rand
                ncfg.android_gcm_time = timezone.localtime()

                ncfg.save()
                ctx["android_client_rand"] = rand

        else:
            ctx["is_android_client"] = False
            ctx["android_client_register"] = False
    except Exception:
        ctx["is_android_client"] = False
        ctx["android_client_register"] = False

    return ctx


def global_custom_theme(request):
    """
    Add custom theme javascript and css.
    """
    today = timezone.localdate()
    theme = {}

    if today.month == 3 and (14 <= today.day <= 16):
        theme = {"css": "themes/piday/piday.css"}

    return {"theme": theme}


def show_homecoming(request):
    """
    Return whether to show homecoming ribbon/scores
    """
    return {"show_homecoming": settings.HOCO_START_DATE <= timezone.localdate() <= settings.HOCO_END_DATE}


def _get_current_ip(request):
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        ip = x_real_ip.split(",", 1)[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def is_tj_ip(request):
    """
    Return whether the request IP is in the TJ range.

    Returns:
        Whether the IP associated with a request is within the TJ IP range.
    """
    ip = _get_current_ip(request)

    return {"is_tj_ip": (ip in settings.TJ_IPS)}


def show_bus_button(request):
    """
    Export if user has access to view the bus button.

    The user must either be a bus admin or be within an hour of the end
    """
    is_bus_admin = request.user.is_authenticated and request.user.has_admin_permission("bus")
    now = timezone.localtime()
    window = datetime.timedelta(hours=1)
    today = Day.objects.today()
    if settings.ENABLE_BUS_DRIVER:
        return {"show_bus_nav": True}
    try:
        if today is None or today.day_type.no_school:
            return {"show_bus_nav": is_bus_admin and settings.ENABLE_BUS_APP}

        end_of_day = Day.objects.today().end_time.date_obj(now.date())
        is_valid_time = end_of_day - window < now < end_of_day + window
        return {"show_bus_nav": (is_bus_admin or is_valid_time) and settings.ENABLE_BUS_APP}

    except AttributeError:
        return {"show_bus_nav": is_bus_admin and settings.ENABLE_BUS_APP}


def enable_dark_mode(request):
    """
    Export whether dark mode is enabled.
    """
    return {"dark_mode_enabled": dark_mode_enabled(request)}


def oauth_toolkit(request):
    """
    Export application tokens arranged by application on OAuth pages.
    """
    if request.user.is_authenticated:
        try:
            resolve_match = resolve(request.path)
        except Resolver404:
            pass
        else:
            if resolve_match.namespaces == ["oauth2_provider"] and resolve_match.url_name == "authorized-token-list":
                applications_tokens = [
                    (application, application.accesstoken_set.filter(user=request.user))
                    for application in Application.objects.filter(accesstoken__user=request.user).distinct()
                ]
                return {"applications_tokens": applications_tokens}

    return {}


def settings_export(request):
    """
    Export all Django settings to templates
    """
    return {"DJANGO_SETTINGS": settings}
