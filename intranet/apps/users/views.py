# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves import cStringIO as StringIO
import io
import logging
import os
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from .models import User, Grade
from ..eighth.models import EighthBlock, EighthSignup
from intranet import settings

logger = logging.getLogger(__name__)


@login_required
def profile_view(request, user_id=None):
    """Displays a view of a user's profile.

    Args:
        user_id
            The ID of the user whose profile is being viewed. If not
            specified, show the user's own profile.

    """
    if user_id is not None:
        profile_user = User.get_user(id=user_id)
        if profile_user is None:
            raise Http404
    else:
        profile_user = request.user

    eighth_schedule = []
    start_block = EighthBlock.objects.get_first_upcoming_block()
    blocks = [start_block] + list(start_block.next_blocks(5))

    for block in blocks:
        sch = {}
        sch["block"] = block
        try:
            sch["signup"] = EighthSignup.objects.get(scheduled_activity__block=block, user=profile_user)
        except EighthSignup.DoesNotExist:
            sch["signup"] = None
        eighth_schedule.append(sch)


    context = {
        "profile_user": profile_user,
        "eighth_schedule": eighth_schedule
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
    user = User.get_user(id=user_id)
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
                if user.user_type == "tjhsstTeacher":
                    current_grade = 12
                else:
                    current_grade = int(user.grade)
                    if current_grade == 13:
                        current_grade = 12

                for i in reversed(range(9, current_grade + 1)):
                    data = user.photo_binary(Grade.names[i - 9])
                    if data:
                        break
                if data is None:
                    image_buffer = io.open(default_image_path, mode="rb")
                else:
                    image_buffer = StringIO(data)

            # Exclude 'graduate' from names array
            elif preferred in Grade.names[:-1]:
                data = user.photo_binary(preferred)

                if data:
                    image_buffer = StringIO(data)
                else:
                    image_buffer = io.open(default_image_path, mode="rb")
            else:
                image_buffer = io.open(default_image_path, mode="rb")
        else:
            data = user.photo_binary(year)
            if data:
                image_buffer = StringIO(data)
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
