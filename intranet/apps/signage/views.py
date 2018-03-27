# -*- coding: utf-8 -*-

import logging

from django import http
from django.conf import settings
from django.shortcuts import render
# from django.views.decorators.clickjacking import xframe_options_exempt

from .models import Sign
from ..eighth.models import EighthBlock
from ..eighth.serializers import EighthBlockDetailSerializer
from ..users.models import User
from ...utils.serialization import safe_json

logger = logging.getLogger(__name__)


def check_show_eighth(now):
    next_block = EighthBlock.objects.get_first_upcoming_block()
    if next_block:
        if next_block.date != now.date():
            return False

    return (8 < now.time().hour < 16)


def check_internal_ip(request):
    remote_addr = (request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", ""))
    if not request.user.is_authenticated and remote_addr not in settings.INTERNAL_IPS:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)


def signage_display(request, display_id):
    check_ip = check_internal_ip(request)
    if check_ip:
        return check_ip
    sign = Sign.objects.get(display=display_id)
    context = {
        "sign": sign
    }
    return render(request, "signage/base.html", context)


# @xframe_options_exempt
def eighth_signage(request, block_id=None, block_increment=0):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    if block_id is None:
        next_block = EighthBlock.objects.get_first_upcoming_block()
        if next_block is not None:
            block_id = next_block.id
        else:
            last_block = EighthBlock.objects.order_by("date").last()
            if last_block is not None:
                block_id = last_block.id

    if "block_increment" in request.GET:
        block_increment = request.GET.get("block_increment", 0)

    try:
        block_increment = int(block_increment)
    except ValueError:
        block_increment = 0

    block = None
    if block_increment > 0:
        next_blocks = next_block.next_blocks()
        if next_blocks.count() >= block_increment:
            block = next_blocks[block_increment - 1]

    if not block:
        try:
            block = (EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(id=block_id))
        except EighthBlock.DoesNotExist:
            if EighthBlock.objects.count() == 0:
                # No blocks have been added yet
                return render(request, "eighth/display.html", {"no_blocks": True})
            else:
                # The provided block_id is invalid
                raise http.Http404

    user = User.get_signage_user()

    serializer_context = {"request": request, "user": user}
    block_info = EighthBlockDetailSerializer(block, context=serializer_context).data
    try:
        reload_mins = float(request.GET.get("reload_mins") or 5)
    except Exception:
        reload_mins = 5

    touch_signage = ("touch" in request.GET)

    next_block = list(block.next_blocks(1))
    if next_block:
        next_block = next_block[0]
        if next_block.date != block.date:
            next_block = None

    prev_block = list(block.previous_blocks(1))
    if prev_block:
        prev_block = prev_block[0]
        if prev_block.date != block.date:
            prev_block = None

    context = {
            "user": user,
            "real_user": request.user,
            "block_info": block_info,
            "activities_list": safe_json(block_info["activities"]),
            "active_block": block,
            "active_block_current_signup": None,
            "no_title": ("no_title" in request.GET),
            "no_detail": not ("detail" in request.GET),
            "no_rooms": ("no_rooms" in request.GET),
            "use_scroll": False if touch_signage else ("no_scroll" not in request.GET),
            "do_reload": ("no_reload" not in request.GET),
            "preload_background": True,
            "reload_mins": reload_mins,
            "no_user_display": True,
            "no_fav": True,
            "touch_signage": touch_signage,
            "next_block": next_block,
            "prev_block": prev_block
            }

    return render(request, "eighth/display.html", context)
