import json
import logging

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from ..schedule.notifications import chrome_getdata_check
from .models import GCMNotification, NotificationConfig

logger = logging.getLogger(__name__)


@csrf_exempt
def android_setup_view(request):
    """Set up a GCM session.
    This does *not* require a valid login session. Instead, a token from the client
    session is sent to the Android backend, which queries a POST request to this view.

    The "android_gcm_rand" is randomly set when the Android app is detected through
    the user agent. If it has the same value, it is assumed to be correct.
    """
    if request.method == "POST":
        if "user_token" in request.POST and "gcm_token" in request.POST:
            user_token = request.POST.get("user_token")
            gcm_token = request.POST.get("gcm_token")

            try:
                ncfg = NotificationConfig.objects.get(android_gcm_rand=user_token)
            except NotificationConfig.DoesNotExist:
                return HttpResponse('{"error":"Invalid data."}', content_type="text/json")

            ncfg.gcm_token = gcm_token
            ncfg.android_gcm_rand = None
            ncfg.android_gcm_date = None
            ncfg.save()
            return HttpResponse('{"success":"Now registered."}', content_type="text/json")
    return HttpResponse('{"error":"Invalid arguments."}', content_type="text/json")


@csrf_exempt
def chrome_getdata_view(request):
    """Get the data of the last notification sent to the current user.

    This is needed because Chrome, as of version 44, doesn't support
    sending a data payload to a notification. Thus, information on what
    the notification is actually for must be manually fetched.

    """
    data = {}
    if request.user.is_authenticated:
        # authenticated session
        notifs = GCMNotification.objects.filter(sent_to__user=request.user).order_by("-time")
        if notifs.count() > 0:
            notif = notifs.first()
            ndata = notif.data
            if "title" in ndata and "text" in ndata:
                data = {
                    "title": ndata["title"] if "title" in ndata else "",
                    "text": ndata["text"] if "text" in ndata else "",
                    "url": ndata["url"] if "url" in ndata else "",
                }
            else:
                schedule_chk = chrome_getdata_check(request)
                if schedule_chk:
                    data = schedule_chk
        else:
            schedule_chk = chrome_getdata_check(request)
            if schedule_chk:
                data = schedule_chk
            else:
                return HttpResponse("null", content_type="text/json")
    else:
        schedule_chk = chrome_getdata_check(request)
        if schedule_chk:
            data = schedule_chk
        else:
            data = {"title": "Check Intranet", "text": "You have a new notification that couldn't be loaded right now."}
    j = json.dumps(data)
    return HttpResponse(j, content_type="text/json")


@login_required
def chrome_setup_view(request):
    """Set up a browser-side GCM session.
    This *requires* a valid login session. A "token" POST parameter is saved under the "gcm_token"
    parameter in the logged in user's NotificationConfig.

    """
    token = None
    if request.method == "POST":
        if "token" in request.POST:
            token = request.POST.get("token")

    if not token:
        return HttpResponse('{"error":"Invalid data."}', content_type="text/json")
    ncfg, _ = NotificationConfig.objects.get_or_create(user=request.user)
    ncfg.gcm_token = token
    ncfg.save()
    return HttpResponse('{"success":"Now registered."}', content_type="text/json")


@login_required
def gcm_list_view(request):
    if not request.user.has_admin_permission("notifications"):
        return redirect("index")
    gcm_notifs = GCMNotification.objects.all().order_by("-time")
    posts = []
    for n in gcm_notifs:
        data = json.loads(n.sent_data)
        if "data" not in data:
            continue
        posts.append({"gcm": n, "data": data["data"]})

    context = {"posts": posts}

    return render(request, "notifications/gcm_list.html", context)


def gcm_post(nc_users, data, user=None, request=None):
    if not user:
        user = request.user

    nc_objs = []
    reg_ids = []
    fail_ids = []
    for ncid in nc_users:
        try:
            nc = NotificationConfig.objects.get(id=ncid)
        except NotificationConfig.DoesNotExist:
            continue

        if nc.gcm_token:
            reg_ids.append(nc.gcm_token)
            nc_objs.append(nc)
        else:
            fail_ids.append(ncid)

    headers = {"Content-Type": "application/json", "project_id": settings.GCM_PROJECT_ID, "Authorization": "key={}".format(settings.GCM_AUTH_KEY)}
    postdata = {"registration_ids": reg_ids, "data": data}
    postjson = json.dumps(postdata)
    req = requests.post("https://android.googleapis.com/gcm/send", headers=headers, data=postjson)
    try:
        resp = req.json()
    except ValueError as e:
        logger.debug(e)
    # example output:
    # {"multicast_id":123456,"success":1,"failure":0,"canonical_ids":0,"results":[{"message_id":"0:142%771acd"}]}
    if "multicast_id" in resp:
        n = GCMNotification.objects.create(
            multicast_id=resp["multicast_id"], num_success=resp["success"], num_failure=resp["failure"], user=user, sent_data=json.dumps(data)
        )
        for nc in nc_objs:
            n.sent_to.add(nc)
        n.save()
        return resp, req.text
    return False, req.text


@login_required
def gcm_post_view(request):
    if not request.user.has_admin_permission("notifications"):
        return redirect("index")
    try:
        has_tokens = settings.GCM_AUTH_KEY and settings.GCM_PROJECT_ID
    except AttributeError:
        has_tokens = False

    if not has_tokens:
        messages.error(request, "GCM tokens not installed.")
        return redirect("index")

    # exclude those with no GCM token, or opted out
    nc_all = NotificationConfig.objects.exclude(gcm_token=None).exclude(gcm_optout=True)
    data = {
        "title": request.POST.get("title", "Title"),
        "text": request.POST.get("text", "Text"),
        "url": request.POST.get("url", None),
        "sound": request.POST.get("sound", False),
        "wakeup": request.POST.get("wakeup", False),
        "vibrate": request.POST.get("vibrate", 0),
    }
    context = {"nc_all": nc_all, "has_tokens": has_tokens}

    if request.method == "POST":
        nc_users = request.POST.getlist("nc_users")
        post, reqtext = gcm_post(nc_users, data, request.user)
        if post:
            messages.success(request, "Delivered message: {} success, {} failure".format(post["success"], post["failure"]))
        else:
            messages.error(request, "Failed. {}".format(reqtext))
    return render(request, "notifications/gcm_post.html", context)


def get_gcm_schedule_uids():
    nc_all = NotificationConfig.objects.exclude(gcm_token=None).exclude(gcm_optout=True)
    nc = nc_all.filter(user__receive_schedule_notifications=True)
    return nc.values_list("id", flat=True)
