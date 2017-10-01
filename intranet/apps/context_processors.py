# -*- coding: utf-8 -*-

import datetime
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


def ion_base_url(request):
    """Return the base URL through request.build_absolute_uri for the index page."""
    return {"ion_base_url": request.build_absolute_uri('/')}


def global_warning(request):
    """Display a global warning on all pages throughout the application."""
    global_warning = settings.GLOBAL_WARNING if hasattr(settings, 'GLOBAL_WARNING') else None

    return {"global_warning": global_warning}


def nav_categorizer(request):
    """Determine which top-level nav category (left nav) a request
    falls under
    """

    categories = [(r"^/$", "dashboard"), (r"^/announcements", "dashboard"), (r"^/eighth/admin", "eighth_admin"), (r"^/eighth", "eighth"),
                  (r"^/events", "events"), (r"^/files", "files"), (r"^/printing", "printing"), (r"^/groups", "groups"), (r"^/polls", "polls"),
                  (r"^/board", "board"), (r"/bus", "bus")]

    for pattern, category in categories:
        p = re.compile(pattern)
        if p.match(request.path):
            return {"nav_category": category}

    return {"nav_category": ""}


def mobile_app(request):
    """Determine if the site is being displayed in a WebView from a native application."""

    ctx = {}
    try:
        ua = request.META.get('HTTP_USER_AGENT', '')

        if "IonAndroid: gcmFrame" in ua:
            logger.debug("IonAndroid %s", request.user)

            ctx["is_android_client"] = True
            registered = "appRegistered:False" in ua
            ctx["android_client_registered"] = registered

            if request.user and request.user.is_authenticated:
                """Add/update NotificationConfig object."""
                import binascii
                import os
                from intranet.apps.notifications.models import NotificationConfig
                from datetime import datetime

                ncfg, _ = NotificationConfig.objects.get_or_create(user=request.user)
                if not ncfg.android_gcm_rand:
                    rand = binascii.b2a_hex(os.urandom(32))
                    ncfg.android_gcm_rand = rand
                else:
                    rand = ncfg.android_gcm_rand
                ncfg.android_gcm_time = datetime.now()

                logger.debug("GCM random token generated: %s", rand)
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
    """Add custom theme javascript and css."""
    today = datetime.datetime.now().date()
    theme = {}

    if today.month == 3 and (14 <= today.day <= 16):
        theme = {"css": "themes/piday/piday.css"}

    return {"theme": theme}


def show_homecoming(request):
    """Show homecoming ribbon / scores """
    return {'show_homecoming': settings.HOCO_START_DATE < datetime.date.today() and datetime.date.today() < settings.HOCO_END_DATE}


def _get_current_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',', 1)[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def is_tj_ip(request):
    ip = _get_current_ip(request)

    return {"is_tj_ip": (ip in settings.TJ_IPS)}


def show_bus_button(request):
    is_bus_admin = request.user.is_authenticated and request.user.has_admin_permission("bus")
    now = datetime.datetime.now()
    is_valid_time = (now.hour > 14 and now.minute > 30) \
        and (now.hour < 17 and now.minute < 30)

    return {'show_bus_nav': (is_bus_admin or is_valid_time)}
