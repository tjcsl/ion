""" Signup """
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from rest_framework import generics, views
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from intranet.apps.eighth.serializers import EighthBlockListSerializer, \
    EighthBlockDetailSerializer, EighthActivityDetailSerializer, \
    EighthSignupSerializer
from .common import unmatch, eighth_confirm_view
from ..models import EighthSponsor, EighthRoom, EighthBlock, EighthActivity, \
    EighthSignup, EighthScheduledActivity, EighthScheduledActivityForm
from django.contrib.auth.models import Group
from intranet.apps.auth.decorators import eighth_admin_required, eighth_student_required
from django.contrib.auth.decorators import login_required
import logging
logger = logging.getLogger(__name__)

def signup_student(request, user, block, activity, force=False):
    """Utility method for signing up a student for an eighth period activity.

    Returns:
        The EighthSignup object for the user and EighthScheduledActivity.
    """

    try:
        sch_activity = EighthScheduledActivity.objects.get(
            block=block,
            activity=activity
        )
    except EighthScheduledActivity.DoesNotExist:
        raise Exception("The scheduled activity does not exist.")

    try:
        current_signup = EighthScheduledActivity.objects.get(
            block=block,
            members=user
        )
        # TODO: Better checking here. Maybe something like
        # scheduledActivity.canSignUp(user)
        if current_signup.activity.sticky and not force:
            messages.error(request,
                "{} is stickied into {}.".format(user, current_signup.activity)
            )
        # TODO: BOTH BLOCKS
        #elif current_signup.activity.both_blocks:
        #    raise Exception("This is a both blocks activity: {}" \
        #        .format(current_signup.activity)
        #    )
        else:
            """remove the signup for the previous activity"""
            EighthSignup.objects.get(
                user=user,
                scheduled_activity=current_signup
            ).delete()
    except EighthScheduledActivity.DoesNotExist:
        """They haven't signed up for anything, which is fine."""
        pass

    signup = EighthSignup.objects.create(
        user=user,
        scheduled_activity=sch_activity
    )
    return signup
    """ A sch_activity.members.add() isn't needed -- it's done automatically. """

@eighth_admin_required
def eighth_students_register(request, match=None):
    map = unmatch(match)
    block, activity, group = map.get('block'), map.get('activity'), map.get('group')
    next = request.path.split('eighth/')[1]
    if block is None:
        return redirect("/eighth/choose/block?next="+next)
    if activity is None:
        return redirect("/eighth/choose/activity/block/"+block+"?next="+next)
    if group is None:
        return redirect("/eighth/choose/group?next="+next)
    force = ('force' in request.GET)
    grp = Group.objects.get(id=group)
    act = EighthActivity.objects.get(id=activity)
    blk = EighthBlock.objects.get(id=block)
    if 'confirm' in request.POST:
        users = User.objects.filter(groups=grp)

        for user in users:
            ret = signup_student(request, user, blk, act, force)

        return redirect("/eighth/admin?success=1")
    else:
        return eighth_confirm_view(request,
            "register {} for {} on {}".format(
                grp.name,
                act.name,
                blk
            )
        )

@eighth_student_required
def eighth_signup_view(request, block_id=None):

    if 'confirm' in request.POST:
        """Actually sign up"""
        signup = signup_student(
            request,
            request.user,
            request.POST.get('bid'),
            request.POST.get('aid')
        )

        # TODO: This should be done in the API
        if isinstance(signup, EighthSignup):
            return HttpResponse("success")



    if block_id is None:
        block_id = EighthBlock.objects.get_next_block()

    is_admin = True
    if "user" in request.GET and is_admin:
        user = request.GET["user"]
    else:
        user = request.user.id

    try:
        block = EighthBlock.objects \
                           .prefetch_related("eighthscheduledactivity_set") \
                           .get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise Http404

    surrounding_blocks = block.get_surrounding_blocks()
    schedule = []



    signups = EighthSignup.objects.filter(user=user).select_related("scheduled_activity", "scheduled_activity__activity")
    block_signup_map = {s.scheduled_activity.block.id: s.scheduled_activity.activity.name for s in signups}

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

    """Get the ID of the currently selected activity for the current day,
       so it can be checked in the activity listing."""
    try:
        cur_signup = signups.get(scheduled_activity__block=block)
        cur_signup_id = cur_signup.scheduled_activity.activity.id
    except EighthSignup.DoesNotExist:
        cur_signup_id = None
    context = {
        "page": "eighth",
        "user": user,
        "block_info": block_info,
        "activities_list": JSONRenderer().render(block_info["activities"]),
        "active_block": block,
        "cur_signup_id": cur_signup_id
    }

    return render(request, "eighth/signup.html", context)

class EighthUserSignupList(views.APIView):
    """API endpoint that lists all signups for a certain user
    """
    def get(self, request, user_id):
        signups = EighthSignup.objects.filter(user_id=user_id).prefetch_related("scheduled_activity__block").select_related("scheduled_activity__activity")

        # if block_id is not None:
            # signups = signups.filter(activity__block_id=block_id)

        serializer = EighthSignupSerializer(signups, context={"request": request})
        data = serializer.data

        return Response(data)

class EighthScheduledActivitySignupList(views.APIView):
    """API endpoint that lists all signups for a certain scheduled activity
    """
    def get(self, request, scheduled_activity_id):
        signups = EighthSignup.objects.filter(scheduled_activity__id=scheduled_activity_id)

        serializer = EighthSignupSerializer(signups, context={"request": request})
        data = serializer.data

        return Response(serializer.data)

class EighthSignupDetail(generics.RetrieveAPIView):
    """API endpoint that shows details of an eighth signup
    """
    queryset = EighthSignup.objects.all()
    serializer_class = EighthSignupSerializer

