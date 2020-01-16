import io
import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..auth.decorators import deny_restricted
from ..eighth.models import EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from ..eighth.utils import get_start_date
from .models import Course, Grade, Section

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
        if request.user.is_restricted and user_id != request.user.id:
            return render(request, "error/403.html", {"reason": "You do not have permission to view this page."}, status=403)

        profile_user = get_object_or_404(get_user_model(), id=user_id)
    else:
        profile_user = request.user

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
            # TODO: Capture exception
            sch["signup"] = None
        eighth_schedule.append(sch)

    if profile_user.is_eighth_sponsor:
        sponsor = EighthSponsor.objects.get(user=profile_user)
        start_date = get_start_date(request)
        eighth_sponsor_schedule = (
            EighthScheduledActivity.objects.for_sponsor(sponsor).filter(block__date__gte=start_date).order_by("block__date", "block__block_letter")
        )
        eighth_sponsor_schedule = eighth_sponsor_schedule[:10]
    else:
        eighth_sponsor_schedule = None

    admin_or_teacher = request.user.is_eighth_admin or request.user.is_teacher
    can_view_eighth = profile_user.can_view_eighth or request.user == profile_user
    eighth_restricted_msg = not can_view_eighth and admin_or_teacher

    if not can_view_eighth and not request.user.is_eighth_admin and not request.user.is_teacher:
        eighth_schedule = []

    has_been_nominated = (
        profile_user == request.user and request.user.nomination_votes.filter(position__position_name=settings.NOMINATION_POSITION).exists()
    )

    context = {
        "profile_user": profile_user,
        "eighth_schedule": eighth_schedule,
        "can_view_eighth": can_view_eighth,
        "eighth_restricted_msg": eighth_restricted_msg,
        "eighth_sponsor_schedule": eighth_sponsor_schedule,
        "nominations_active": settings.NOMINATIONS_ACTIVE,
        "nomination_position": settings.NOMINATION_POSITION,
        "has_been_nominated": has_been_nominated,
    }
    return render(request, "users/profile.html", context)


@login_required
def picture_view(request, user_id, year=None):
    """Displays a view of a user's picture.

    Args:
        user_id (str): The ID of the user whose picture is being fetched.
        year (str): The user's picture from this year is fetched. If not
            specified, use the preferred picture.

    """
    user = get_object_or_404(get_user_model(), id=user_id)
    default_image_path = os.path.join(settings.PROJECT_ROOT, "static/img/default_profile_pic.png")

    img = None
    if year is None:
        preferred = user.preferred_photo
        if preferred is None:
            data = user.default_photo
        else:
            data = preferred.binary
    else:
        grade_number = Grade.number_from_name(year)
        if user.photos.filter(grade_number=grade_number).exists():
            data = user.photos.filter(grade_number=grade_number).first().binary
        else:
            data = None

    if data is None:
        img = io.open(default_image_path, mode="rb").read()
    else:
        image_buffer = io.BytesIO(data)

    response = HttpResponse(content_type="image/jpeg")
    response["Content-Disposition"] = "filename={}_{}.jpg".format(user_id, year or preferred)

    if img is None:
        try:
            img = image_buffer.read()
        except UnicodeDecodeError:
            img = io.open(default_image_path, mode="rb").read()
        image_buffer.close()
    response.write(img)

    return response


@login_required
@deny_restricted
def all_courses_view(request):
    context = {"courses": Course.objects.all().distinct()}
    return render(request, "users/all_courses.html", context)


@login_required
@deny_restricted
def courses_by_period_view(request, period_number):
    context = {"courses": Course.objects.filter(sections__period=period_number).distinct()}
    return render(request, "users/all_courses.html", context)


@login_required
@deny_restricted
def course_info_view(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    context = {"course": course}
    return render(request, "users/all_classes.html", context)


@login_required
@deny_restricted
def sections_by_room_view(request, room_number):
    sections = Section.objects.filter(room=room_number).order_by("period")
    if not sections.exists():
        raise Http404
    context = {"room_number": room_number, "classes": sections}
    return render(request, "users/class_room.html", context)


@login_required
@deny_restricted
def section_view(request, section_id):
    section = get_object_or_404(Section, section_id=section_id)
    context = {"class": section}
    return render(request, "users/class.html", context)
