import logging
from datetime import datetime, timedelta

from django import http
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ....utils.serialization import safe_json
from ...auth.decorators import deny_restricted, eighth_admin_required
from ...users.forms import ProfileEditForm
from ..models import EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from ..serializers import EighthBlockDetailSerializer
from ..utils import get_start_date

logger = logging.getLogger(__name__)


def date_fmt(date):
    return datetime.strftime(date, "%Y-%m-%d")


@eighth_admin_required
@deny_restricted
def edit_profile_view(request, user_id=None):
    user = get_object_or_404(get_user_model(), id=user_id)
    # Disable address form temporarily -- okulkarni, 08/30/2018
    address_form = None
    if request.method == "POST":
        user_form = ProfileEditForm(request.POST, instance=user)
        # address_form = AddressForm(request.POST, instance=user.properties.address)
        if user_form.is_valid():
            user = user_form.save()
            counselor_id = user_form.cleaned_data["counselor_id"]
            if counselor_id:
                counselor = get_user_model().objects.get(id=counselor_id)
                user.properties.birthday = user_form.cleaned_data["birthday"]
                user.counselor = counselor
            # user.properties.address = address_form.save()
            # user.properties.save()
            user.save()
            messages.success(request, "Successfully updated student profile.")
        else:
            messages.error(request, "An error occurred updating the student profile.")
    else:
        user_form = ProfileEditForm(
            initial={"counselor_id": "" if not user.counselor else user.counselor.id, "birthday": user.properties.birthday}, instance=user
        )
        # address_form = AddressForm(instance=user.properties.address)

    context = {"profile_user": user, "user_form": user_form, "address_form": address_form}
    return render(request, "eighth/edit_profile.html", context)


def get_profile_context(request, user_id=None, date=None):
    if user_id:
        try:
            profile_user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            raise http.Http404
    else:
        profile_user = request.user
    if profile_user != request.user and not (request.user.is_eighth_admin or request.user.is_teacher):
        return False

    try:
        custom_date_set = False
        if date:
            custom_date_set = True
        elif "date" in request.GET:
            date = request.GET.get("date")
            date = datetime.strptime(date, "%Y-%m-%d")
            custom_date_set = True
        elif "start_date" in request.session:
            date = get_start_date(request)
        else:
            date = timezone.localtime()
    except Exception:
        date = timezone.localtime()

    date_end = date + timedelta(days=14)

    date_previous = date + timedelta(days=-14)
    date_next = date_end

    eighth_schedule = []
    skipped_ahead = False

    blocks_all = EighthBlock.objects.order_by("date", "block_letter").filter(date__gte=date)
    blocks = blocks_all.filter(date__lt=date_end)

    if not blocks:
        blocks = list(blocks_all)[:6]
        skipped_ahead = True
        if blocks:
            date_next = list(blocks)[-1].date + timedelta(days=1)

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
        "eighth_schedule": eighth_schedule,
        "date_previous": date_fmt(date_previous),
        "date_now": date_fmt(date),
        "date_next": date_fmt(date_next),
        "date": date,
        "date_end": date_end,
        "skipped_ahead": skipped_ahead,
        "custom_date_set": custom_date_set,
    }

    if profile_user.is_eighth_sponsor:
        sponsor = EighthSponsor.objects.get(user=profile_user)
        start_date = get_start_date(request)
        eighth_sponsor_schedule = (
            EighthScheduledActivity.objects.for_sponsor(sponsor).filter(block__date__gte=start_date).order_by("block__date", "block__block_letter")
        )
        eighth_sponsor_schedule = eighth_sponsor_schedule[:10]

        context["eighth_sponsor_schedule"] = eighth_sponsor_schedule

    return context


@login_required
@deny_restricted
def profile_view(request, user_id=None):
    context = get_profile_context(request, user_id)
    if context:
        context["show_profile_header"] = request.user.is_eighth_admin
        return render(request, "eighth/profile.html", context)
    else:
        return render(request, "error/403.html", {"reason": "You may only view your own schedule."}, status=403)


@login_required
@deny_restricted
def profile_history_view(request, user_id=None):
    if user_id:
        try:
            profile_user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            raise http.Http404
    else:
        profile_user = request.user

    if profile_user != request.user and not (request.user.is_eighth_admin or request.user.is_teacher):
        return render(request, "error/403.html", {"reason": "You may only view your own schedule."}, status=403)

    if profile_user.is_eighth_sponsor and not profile_user.is_student and request.user.is_eighth_admin:
        return redirect("eighth_admin_sponsor_schedule", profile_user.get_eighth_sponsor().id)

    blocks = EighthBlock.objects.get_blocks_this_year()
    blocks = blocks.filter(locked=True)
    blocks = blocks.order_by("date", "block_letter")

    eighth_schedule = []

    for block in blocks:
        sch = {}
        sch["block"] = block
        try:
            sch["signup"] = EighthSignup.objects.get(scheduled_activity__block=block, user=profile_user)
            sch["highlighted"] = int(request.GET.get("activity") or 0) == sch["signup"].scheduled_activity.activity.id
        except EighthSignup.DoesNotExist:
            sch["signup"] = None
        eighth_schedule.append(sch)

    context = {"profile_user": profile_user, "eighth_schedule": eighth_schedule, "show_profile_header": request.user.is_eighth_admin}

    return render(request, "eighth/profile_history.html", context)


@login_required
@deny_restricted
def profile_often_view(request, user_id=None):
    if user_id:
        try:
            profile_user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            raise http.Http404
    else:
        profile_user = request.user

    if profile_user != request.user and not (request.user.is_eighth_admin or request.user.is_teacher):
        return render(request, "error/403.html", {"reason": "You may only view your own schedule."}, status=403)

    blocks = EighthBlock.objects.get_blocks_this_year()
    blocks = blocks.filter(locked=True)

    signups = EighthSignup.objects.filter(user=profile_user, scheduled_activity__block__in=blocks)
    activities = []
    for sch in signups:
        activities.append(sch.scheduled_activity.activity)

    oftens = []
    unique_activities = set(activities)
    for act in unique_activities:
        oftens.append({"count": activities.count(act), "activity": act})

    oftens = sorted(oftens, key=lambda x: (-1 * x["count"]))

    context = {"profile_user": profile_user, "oftens": oftens, "show_profile_header": request.user.is_eighth_admin}

    return render(request, "eighth/profile_often.html", context)


@login_required
@deny_restricted
def profile_signup_view(request, user_id=None, block_id=None):
    if user_id:
        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            raise http.Http404
    else:
        user = request.user

    if user != request.user and not request.user.is_eighth_admin:
        return render(request, "error/403.html", {"reason": "You may only modify your own schedule."}, status=403)

    if block_id is None:
        return redirect(request, "eighth_profile", user_id)

    try:
        block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(id=block_id)
    except EighthBlock.DoesNotExist:
        if EighthBlock.objects.count() == 0:
            # No blocks have been added yet
            return render(request, "eighth/profile_signup.html", {"no_blocks": True})
        else:
            # The provided block_id is invalid
            raise http.Http404

    serializer_context = {"request": request, "user": user}
    block_info = EighthBlockDetailSerializer(block, context=serializer_context).data
    activities_list = safe_json(block_info["activities"])

    try:
        active_block_current_signup = EighthSignup.objects.get(user=user, scheduled_activity__block__id=block_id)
        active_block_current_signup = active_block_current_signup.scheduled_activity.activity.id
    except EighthSignup.DoesNotExist:
        active_block_current_signup = None

    context = {
        "user": user,
        "real_user": request.user,
        "activities_list": activities_list,
        "active_block": block,
        "active_block_current_signup": active_block_current_signup,
        "show_eighth_profile_link": True,
        "block_info": block_info,
    }
    profile_ctx = get_profile_context(request, user_id, block.date)
    if profile_ctx:
        context.update(profile_ctx)
    return render(request, "eighth/profile_signup.html", context)
