# -*- coding: utf-8 -*-

import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


def ion_base_url(request):
    """Return the base URL through request.build_absolute_uri for the index page."""
    return {"ion_base_url": request.build_absolute_uri('/')}


def global_warning(request):
    """Display a global warning on all pages throughout the application.
    """
    global_warning = settings.GLOBAL_WARNING if hasattr(settings, 'GLOBAL_WARNING') else None

    return {"global_warning": global_warning}


def nav_categorizer(request):
    """Determine which top-level nav category (left nav) a request
    falls under
    """

    categories = [
        (r"^/$", "dashboard"),
        (r"^/announcements", "dashboard"),
        (r"^/eighth/admin", "eighth_admin"),
        (r"^/eighth", "eighth"),
        (r"^/events", "events"),
        (r"^/files", "files"),
        (r"^/groups", "groups"),
        (r"^/polls", "polls")
    ]

    for pattern, category in categories:
        p = re.compile(pattern)
        if p.match(request.path):
            return {"nav_category": category}

    return {"nav_category": ""}


def mobile_app(request):
    """Determine if the site is being displayed in a WebView from
    a native application
    """

    ctx = {}
    try:
        ua = request.META.get('HTTP_USER_AGENT', '')

        if "IonAndroid: gcmFrame" in ua:
            logger.debug("IonAndroid %s", request.user)

            ctx["is_android_client"] = True
            registered = "appRegistered:False" in ua
            ctx["android_client_registered"] = registered

            if request.user and request.user.is_authenticated():
                """Add/update NotificationConfig object"""
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
