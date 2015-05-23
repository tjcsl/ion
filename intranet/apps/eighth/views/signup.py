# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.renderers import JSONRenderer
from ...users.models import User
from ..exceptions import SignupException
from ..models import (
    EighthBlock, EighthSignup, EighthScheduledActivity, EighthActivity
)
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

        try:
            user = User.get_user(id=uid)
        except User.DoesNotExist:
            return http.HttpResponseNotFound("Given user does not exist.")

        try:
            scheduled_activity = (EighthScheduledActivity.objects
                                                         .exclude(activity__deleted=True)
                                                         .exclude(cancelled=True)
                                                         .get(block=bid,
                                                              activity=aid))
            if not request.is_eighth_admin():
                scheduled_activity = scheduled_activity.exclude(activity__administrative=True)

        except EighthScheduledActivity.DoesNotExist:
            return http.HttpResponseNotFound("Given activity not scheduled "
                                             "for given block.")

        try:
            scheduled_activity.add_user(user, request)
        except SignupException as e:
            show_admin_messages = (request.user.is_eighth_admin and
                                   not request.user.is_student)
            return e.as_response(admin=show_admin_messages)

        return http.HttpResponse("Successfully signed up for activity.")
    else:
        if block_id is None:
            next_block = EighthBlock.objects.get_first_upcoming_block()
            if next_block is not None:
                block_id = next_block.id
            else:
                last_block = EighthBlock.objects.order_by("date").last()
                if last_block is not None:
                    block_id = last_block.id

        if "user" in request.GET and request.user.is_eighth_admin:
            try:
                user = User.get_user(id=request.GET["user"])
            except (User.DoesNotExist, ValueError):
                raise http.Http404
        else:
            if request.user.is_student:
                user = request.user
            else:
                return redirect("eighth_admin_dashboard")

        try:
            block = (EighthBlock.objects
                                .prefetch_related("eighthscheduledactivity_set")
                                .get(id=block_id))
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
        block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity for s in signups}

        for b in surrounding_blocks:
            info = {
                "id": b.id,
                "block_letter": b.block_letter,
                "current_signup": getattr(block_signup_map.get(b.id, {}), "activity", None),
                "current_signup_cancelled": getattr(block_signup_map.get(b.id, {}), "cancelled", False),
                "locked": b.locked
            }

            if len(schedule) and schedule[-1]["date"] == b.date:
                schedule[-1]["blocks"].append(info)
            else:
                day = {}
                day["date"] = b.date
                day["blocks"] = []
                day["blocks"].append(info)
                schedule.append(day)

        serializer_context = {
            "request": request,
            "user": user
        }
        block_info = EighthBlockDetailSerializer(block, context=serializer_context).data
        block_info["schedule"] = schedule

        try:
            active_block_current_signup = block_signup_map[int(block_id)].activity.id
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


@login_required
def toggle_favorite_view(request):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"])
    if not ("aid" in request.POST and request.POST["aid"].isdigit()):
        http.HttpResponseBadRequest("Must specify an integer aid")

    aid = request.POST["aid"]
    activity = get_object_or_404(EighthActivity, id=aid)
    if activity.favorites.filter(id=request.user.id).exists():
        activity.favorites.remove(request.user)
        return http.HttpResponse("Unfavorited activity.")
    else:
        activity.favorites.add(request.user)
        return http.HttpResponse("Favorited activity.")
