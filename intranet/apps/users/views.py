# -*- coding: utf-8 -*-

import csv
import io
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.core.exceptions import MultipleObjectsReturned

from raven.contrib.django.raven_compat.models import client

from .models import Class, Grade, User
from ..eighth.models import (EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor)
from ..eighth.utils import get_start_date

logger = logging.getLogger(__name__)


@login_required
def profile_view(request, user_id=None):
    """Displays a view of a user's profile.

    Args:
        user_id
            The ID of the user whose profile is being viewed. If not
            specified, show the user's own profile.

    """
    if request.user.is_eighthoffice and "full" not in request.GET and user_id is not None:
        return redirect("eighth_profile", user_id=user_id)

    if user_id is not None:
        try:
            profile_user = User.get_user(id=user_id)

            if profile_user is None:
                raise Http404
        except User.DoesNotExist:
            raise Http404
    else:
        profile_user = request.user

    if "clear_cache" in request.GET and request.user.is_eighth_admin:
        profile_user.clear_cache()
        messages.success(request, "Cleared cache for {}".format(profile_user))
        return redirect("/profile/{}".format(profile_user.id))

    num_blocks = 6

    eighth_schedule = []
    start_block = EighthBlock.objects.get_first_upcoming_block()

    blocks = []
    if start_block:
        blocks = [start_block] + list(start_block.next_blocks(num_blocks - 1))

    for block in blocks:
        sch = {"block": block}
        try:
            sch["signup"] = EighthSignup.objects.get(scheduled_activity__block=block, user=profile_user)
        except EighthSignup.DoesNotExist:
            sch["signup"] = None
        except MultipleObjectsReturned:
            client.captureException()
            sch["signup"] = None
        eighth_schedule.append(sch)

    if profile_user.is_eighth_sponsor:
        sponsor = EighthSponsor.objects.get(user=profile_user)
        start_date = get_start_date(request)
        eighth_sponsor_schedule = (EighthScheduledActivity.objects.for_sponsor(sponsor).filter(block__date__gte=start_date).order_by(
            "block__date", "block__block_letter"))
        eighth_sponsor_schedule = eighth_sponsor_schedule[:10]
    else:
        eighth_sponsor_schedule = None

    admin_or_teacher = (request.user.is_eighth_admin or request.user.is_teacher)
    can_view_eighth = (profile_user.can_view_eighth or request.user == profile_user)
    eighth_restricted_msg = (not can_view_eighth and admin_or_teacher)

    if not can_view_eighth and not request.user.is_eighth_admin and not request.user.is_teacher:
        eighth_schedule = []

    has_been_nominated = profile_user.username in [
        u.nominee.username for u in request.user.nomination_votes.filter(position__position_name=settings.NOMINATION_POSITION)
    ]
    context = {
        "profile_user": profile_user,
        "eighth_schedule": eighth_schedule,
        "can_view_eighth": can_view_eighth,
        "eighth_restricted_msg": eighth_restricted_msg,
        "eighth_sponsor_schedule": eighth_sponsor_schedule,
        "nominations_active": settings.NOMINATIONS_ACTIVE,
        "nomination_position": settings.NOMINATION_POSITION,
        "has_been_nominated": has_been_nominated
    }
    return render(request, "users/profile.html", context)


@login_required
def picture_view(request, user_id, year=None):
    """Displays a view of a user's picture.

    Args:
        user_id
            The ID of the user whose picture is being fetched.
        year
            The user's picture from this year is fetched. If not
            specified, use the preferred picture.

    """
    try:
        user = User.get_user(id=user_id)
    except User.DoesNotExist:
        raise Http404
    default_image_path = os.path.join(settings.PROJECT_ROOT, "static/img/default_profile_pic.png")

    if user is None:
        raise Http404
    else:
        if year is None:
            preferred = user.preferred_photo
            if preferred is not None:
                if preferred.endswith("Photo"):
                    preferred = preferred[:-len("Photo")]

            if preferred == "AUTO":
                data = user.default_photo()
                if data is None:
                    image_buffer = io.open(default_image_path, mode="rb")
                else:
                    image_buffer = io.BytesIO(data)

            # Exclude 'graduate' from names array
            elif preferred in Grade.names:
                data = user.photo_binary(preferred)

                if data:
                    image_buffer = io.BytesIO(data)
                else:
                    image_buffer = io.open(default_image_path, mode="rb")
            else:
                image_buffer = io.open(default_image_path, mode="rb")
        else:
            data = user.photo_binary(year)
            if data:
                image_buffer = io.BytesIO(data)
            else:
                image_buffer = io.open(default_image_path, mode="rb")

        response = HttpResponse(content_type="image/jpeg")
        response["Content-Disposition"] = "filename={}_{}.jpg".format(user_id, year or preferred)
        try:
            img = image_buffer.read()
        except UnicodeDecodeError:
            img = io.open(default_image_path, mode="rb").read()

        image_buffer.close()
        response.write(img)

        return response
