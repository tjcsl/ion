# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import logging

logger = logging.getLogger(__name__)

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

    ua = request.META.get('HTTP_USER_AGENT', '')

    if "IonAndroid: gcmFrame" in ua:
        logger.debug("IonAndroid")
        ctx["is_android_client"] = True
        registered = "appRegistered:False" in ua
        ctx["android_client_registered"] = registered

        if request.user and request.user.is_authenticated():
            """Add/update NotificationConfig object"""
            import binascii
            import os
            from intranet.apps.notifications.models import NotificationConfig
            from datetime import datetime

            ncfg, created = NotificationConfig.objects.get_or_create(user__id=request.user.id)
            if not ncfg.android_gcm_rand:
                rand = binascii.b2a_hex(os.urandom(32))
                ncfg.android_gcm_rand = rand
            else:
                rand = ncfg.android_gcm_rand
            ncfg.android_gcm_time = datetime.now()
            
            logger.debug("GCM random token generated: {}".format(rand))
            ncfg.save()
            ctx["android_client_rand"] = rand

    else:
        ctx["is_android_client"] = False
        ctx["android_client_register"] = False

    return ctx