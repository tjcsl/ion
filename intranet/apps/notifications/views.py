# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .models import NotificationConfig
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import logging

logger = logging.getLogger(__name__)
@csrf_exempt
def android_setup_view(request):
    """Set up a GCM session.
    This does *not* require a valid login session. Instead, a token from the client
    session is sent to the Android backend, which queries a POST request to this view.

    The "android_gcm_rand" is randomly set when the Android app is detected through
    the user agent. If it has the same value, it is assumed to be correct.
    """

    logger.debug(request.POST)
    if request.method == "POST":
        if "user_token" in request.POST and "gcm_token" in request.POST:
            user_token = request.POST.get("user_token")
            gcm_token = request.POST.get("gcm_token")

            logger.debug(user_token)
            logger.debug(gcm_token)
            try:
                ncfg = NotificationConfig.objects.get(android_gcm_rand=user_token)
            except NotificationConfig.DoesNotExist:
                logger.debug("No pair")
                return HttpResponse('{"error":"Invalid data."}', content_type="text/json")

            ncfg.android_gcm_token = gcm_token
            ncfg.android_gcm_rand = None
            ncfg.android_gcm_date = None
            ncfg.save()
            return HttpResponse('{"success":"Now registered."}', content_type="text/json")
    return HttpResponse('{"error":"Invalid arguments."}', content_type="text/json")


