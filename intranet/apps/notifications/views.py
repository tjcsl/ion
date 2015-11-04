# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json
from django.contrib import messages
from .models import NotificationConfig, GCMNotification
from ... import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import redirect, render

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


@login_required
def gcm_list_view(request):
    if not request.user.has_admin_permission("notifications"):
        return redirect("index")
    gcm_notifs = GCMNotification.objects.all().order_by("-time")
    posts = []
    for n in gcm_notifs:
        posts.append({
            "gcm": n,
            "data": json.loads(n.sent_data)["data"]
        })

    context = {
        "posts": posts
    }

    return render(request, "notifications/gcm_list.html", context)


@login_required
def gcm_post_view(request):
    if not request.user.has_admin_permission("notifications"):
        return redirect("index")

    try:
        has_tokens = (settings.GCM_AUTH_KEY and settings.GCM_PROJECT_ID)
    except AttributeError:
        has_tokens = False

    if not has_tokens:
        messages.error(request, "GCM tokens not installed.")
        return redirect("index")

    # exclude those with no GCM token and those who have opted out
    nc_all = NotificationConfig.objects.exclude(android_gcm_token=None, android_gcm_optout=True)
    context = {
        "nc_all": nc_all,
        "has_tokens": has_tokens
    }

    if request.method == "POST":

        nc_objs = []
        reg_ids = []

        fail_ids = []
        nc_users = request.POST.getlist("nc_users")
        logger.debug(nc_users)
        for ncid in nc_users:
            try:
                nc = NotificationConfig.objects.get(id=ncid)
            except NotificationConfig.DoesNotExist:
                continue

            if nc.android_gcm_token and not nc.android_gcm_optout:
                reg_ids.append(nc.android_gcm_token)
                nc_objs.append(nc)
            else:
                fail_ids.append(ncid)

        logger.debug(nc_objs)
        logger.debug(reg_ids)
        headers = {
            "Content-Type": "application/json",
            "project_id": settings.GCM_PROJECT_ID,
            "Authorization": "key={}".format(settings.GCM_AUTH_KEY)
        }
        data = {
            "registration_ids": reg_ids,
            "data": {
                "title": request.POST.get("title", "Title"),
                "text": request.POST.get("text", "Text"),
                "url": request.POST.get("url", None),
                "sound": request.POST.get("sound", False),
                "wakeup": request.POST.get("wakeup", False),
                "vibrate": request.POST.get("vibrate", 0)
            }
        }
        logger.debug(json.dumps(data))
        req = requests.post("https://android.googleapis.com/gcm/send", headers=headers, data=json.dumps(data))
        logger.debug(req.text)
        resp = req.json()
        # example output:
        # {"multicast_id":123456,"success":1,"failure":0,"canonical_ids":0,"results":[{"message_id":"0:142%771acd"}]}
        logger.debug(resp)
        if "multicast_id" in resp:
            n = GCMNotification.objects.create(multicast_id=resp["multicast_id"],
                                               num_success=resp["success"],
                                               num_failure=resp["failure"],
                                               user=request.user,
                                               sent_data=json.dumps(data))
            for nc in nc_objs:
                n.sent_to.add(nc)
            n.save()
            logger.debug(n)
            messages.success(request, "Delivered message: {} success, {} failure".format(resp["success"], resp["failure"]))
        else:
            messages.error(request, "Failed. {}".format(req.text))

    return render(request, "notifications/gcm_post.html", context)
