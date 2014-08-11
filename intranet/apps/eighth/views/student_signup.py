# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from rest_framework.renderers import JSONRenderer
from ...users.models import User
from ..models import EighthBlock, EighthSignup, EighthScheduledActivity
from ..serializers import EighthBlockDetailSerializer


logger = logging.getLogger(__name__)


@login_required
def eighth_signup_view(request, block_id=None):
    if request.method == "POST":
        for field in ("uid", "bid", "aid"):
            if not (field in request.POST and request.POST[field].isdigit()):
                return http.HttpResponseBadRequest(field + " must be an "
                                                   "integer")

        uid = request.POST["uid"]
        bid = request.POST["bid"]
        aid = request.POST["aid"]

        if uid != request.user.id and not request.user.is_eighth_admin:
            return http.HttpResponseForbidden("You may not sign up this "
                                              "student for activities.")

        try:
            scheduled_activity = EighthScheduledActivity.objects \
                                                        .exclude(activity__deleted=True) \
                                                        .exclude(cancelled=True) \
                                                        .get(block=bid,
                                                             activity=aid)
        except EighthScheduledActivity.DoesNotExist:
            return http.HttpResponseNotFound("Given activity not scheduled "
                                             "for given block.")

        try:
            user = User.objects.get(id=uid)
        except User.DoesNotExist:
            return http.HttpResponseNotFound("Given user does not exist.")

        try:
            existing_signup = EighthSignup.objects \
                                          .get(user=user,
                                               scheduled_activity__block=bid)
            existing_signup.scheduled_activity = scheduled_activity
            existing_signup.save()
        except EighthSignup.DoesNotExist:
            pass
            EighthSignup.objects.create(user=user,
                                        scheduled_activity=scheduled_activity)

        return http.HttpResponse("Successfully signed up for activity.")
    else:
        if block_id is None:
            next_block = EighthBlock.objects.get_first_upcoming_block()
            if next_block is not None:
                block_id = next_block.id

        if "user" in request.GET and request.user.is_eighth_admin:
            try:
                user = User.get_and_propogate_user(id=request.GET["user"])
            except User.DoesNotExist:
                raise http.Http404
        else:
            if request.user.is_student:
                user = request.user
            else:
                return redirect("index")

        try:
            block = EighthBlock.objects \
                               .prefetch_related("eighthscheduledactivity_set") \
                               .get(id=block_id)
        except EighthBlock.DoesNotExist:
            if EighthBlock.objects.count() == 0:
                # No blocks have been added yet
                return render(request, "eighth/signup.html", {"no_blocks": True})
            else:
                # The provided block_id is invalid
                raise http.Http404

        surrounding_blocks = block.get_surrounding_blocks()
        schedule = []

        signups = EighthSignup.objects.filter(user=user).select_related("scheduled_activity__block", "scheduled_activity__activity")
        block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity.activity for s in signups}

        for b in surrounding_blocks:
            info = {
                "id": b.id,
                "block_letter": b.block_letter,
                "current_signup": block_signup_map.get(b.id, "")
            }

            if len(schedule) and schedule[-1]["date"] == b.date:
                schedule[-1]["blocks"].append(info)
            else:
                day = {}
                day["date"] = b.date
                day["blocks"] = []
                day["blocks"].append(info)
                schedule.append(day)

        block_info = EighthBlockDetailSerializer(block, context={"request": request}).data
        block_info["schedule"] = schedule

        try:
            active_block_current_signup = block_signup_map[int(block_id)].id
        except KeyError:
            active_block_current_signup = None

        context = {
            "user": user,
            "block_info": block_info,
            "activities_list": JSONRenderer().render(block_info["activities"]),
            "active_block": block,
            "active_block_current_signup": active_block_current_signup
        }

        return render(request, "eighth/signup.html", context)
