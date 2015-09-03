# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves import cStringIO as StringIO
import io
import logging
import os
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from .models import User, Grade, Class
from ..eighth.models import EighthBlock, EighthSignup, EighthScheduledActivity, EighthSponsor
from intranet import settings
from intranet.db.ldap_db import LDAPConnection, LDAPFilter

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

    num_blocks = 6

    eighth_schedule = []
    start_block = EighthBlock.objects.get_first_upcoming_block()
    if start_block:
        blocks = [start_block] + list(start_block.next_blocks(num_blocks-1))
    else:
        blocks = []

    for block in blocks:
        sch = {}
        sch["block"] = block
        try:
            sch["signup"] = EighthSignup.objects.get(scheduled_activity__block=block, user=profile_user)
        except EighthSignup.DoesNotExist:
            sch["signup"] = None
        eighth_schedule.append(sch)

    if profile_user.is_eighth_sponsor:
        sponsor = EighthSponsor.objects.get(user=profile_user)

        logger.debug("Eighth sponsor {}".format(sponsor))

        eighth_sponsor_schedule = []
        if start_block:
            activities_sponsoring = (EighthScheduledActivity.objects.for_sponsor(sponsor)
                                                                    .filter(block__date__gt=start_block.date))
            logger.debug(activities_sponsoring)
            surrounding_blocks = [start_block] + list(start_block.next_blocks()[:num_blocks-1])
            for b in surrounding_blocks:
                sponsored_for_block = activities_sponsoring.filter(block=b)
                for schact in sponsored_for_block:
                    eighth_sponsor_schedule.append(schact)

    else:
        eighth_sponsor_schedule = None

    context = {
        "profile_user": profile_user,
        "eighth_schedule": eighth_schedule,
        "eighth_sponsor_schedule": eighth_sponsor_schedule
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
                if user.user_type == "tjhsstTeacher":
                    current_grade = 12
                else:
                    current_grade = int(user.grade)
                    if current_grade > 12:
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
            elif preferred in Grade.names:
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

@login_required
def class_section_view(request, section_id):
    c = Class(id=section_id)

    attrs = {
        "name": c.name,
        "students": sorted(c.students, key=lambda x: (x.last_name, x.first_name)),
        "teacher": c.teacher,
        "quarters": c.quarters,
        "periods": c.periods,
        "course_length": c.course_length,
        "room_number": c.room_number,
        "class_id": c.class_id,
        "section_id": c.section_id,
        "sections": c.sections
    }

    context = {
        "class": attrs
    }

    return render(request, "users/class.html", context)

@login_required
def class_room_view(request, room_id):
    c = LDAPConnection()
    room_id = LDAPFilter.escape(room_id)
    
    classes = c.search("ou=schedule,dc=tjhsst,dc=edu", 
                       "(&(objectClass=tjhsstClass)(roomNumber={}))".format(room_id),
                       ["tjhsstSectionId"]
    )


    if len(classes) > 0:
        schedule = []
        for row in classes:
            class_dn = row[0]
            class_object = Class(dn=class_dn)
            sortvalue = class_object.sortvalue
            schedule.append((sortvalue, class_object))

        ordered_schedule = sorted(schedule, key=lambda e: e[0])
        classes_objs = list(zip(*ordered_schedule)[1]) # The class objects
    else:
        classes_objs = []
        raise Http404

    context = {
        "room": room_id,
        "classes": classes_objs
    }

    return render(request, "users/class_room.html", context)

@login_required
def all_classes_view(request):
    c = LDAPConnection()
    
    classes = c.search("ou=schedule,dc=tjhsst,dc=edu", 
                       "objectClass=tjhsstClass",
                       ["tjhsstSectionId"]
    )

    logger.debug("{} classes found.".format(len(classes)))

    if len(classes) > 0:
        schedule = []
        for row in classes:
            class_dn = row[0]
            class_object = Class(dn=class_dn)
            sortvalue = class_object.sortvalue
            schedule.append((sortvalue, class_object))

        ordered_schedule = sorted(schedule, key=lambda e: e[0])
        classes_objs = list(zip(*ordered_schedule)[1]) # The class objects
    else:
        classes_objs = []
        raise Http404

    context = {
        "classes": classes_objs
    }

    return render(request, "users/all_classes.html", context)