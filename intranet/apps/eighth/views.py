import logging
import time
import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from .models import EighthSponsor, EighthRoom, EighthBlock, EighthActivity, EighthSignup, EighthScheduledActivity
from rest_framework import generics, views
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from .serializers import EighthBlockListSerializer, \
    EighthBlockDetailSerializer, EighthActivityDetailSerializer, \
    EighthSignupSerializer
from intranet.apps.auth.decorators import *
logger = logging.getLogger(__name__)

def unmatch(match):
    """Takes a string like block/1/activity/2/group/3 and
       returns a dictionary of {'block': 1, 'activity': 2, 'group': 3}
    """

    if match is None:
        return {}

    spl = match.split('/')
    keys = spl[::2]
    values = spl[1::2]
    return dict(zip(keys, values))

def parse_date(date):
    """Takes a string of a date like 04/01/2014 and
       returns a datetime object used in a DateField
    """
    # Make a time.struct_time object out of the string
    structtime = time.strptime(date, "%m/%d/%Y")
    # Convert to datetime format
    dtime = datetime.datetime(*structtime[:6])
    return dtime

@login_required
def eighth_redirect_view(request):
    if request.user.is_eighth_admin:
        pg = "admin"
    elif request.user.is_teacher:
        pg = "teacher"
    elif request.user.is_student:
        pg = "signup"
    else:
        pg = ".."
    return redirect("/eighth/" + pg)

@eighth_admin_required
def eighth_admin_view(request):
    return render(request, "eighth/admin.html", {
        "page": "eighth_admin",
        "success": 'success' in request.POST
    })

@eighth_admin_required
def eighth_choose_block(request):
    next = request.GET.get('next', 'signup')

    blocks = EighthBlock.objects.get_current_blocks()
    return render(request, "eighth/choose_block.html", {
        "page": "eighth_admin",
        "blocks": blocks,
        "next": "/eighth/{}block/".format(next)
    })

@eighth_admin_required
def eighth_choose_activity(request, block_id=None):
    next = request.GET.get('next', '')
    context = {
        "page": "eighth_admin",
        "next": "/eighth/{}activity/".format(next)
    }
    if 'add' in request.GET:
        context["sponsors"] = EighthSponsor.objects.all()
        context["rooms"] = EighthRoom.objects.all()

    if block_id is None:
        """ show all activities """
        activities = EighthActivity.objects.all().order_by("name")
    else:
        activities = []
        schactivities = EighthScheduledActivity.objects \
                            .filter(block__id=block_id) \
                            .order_by("activity__name")
        for schact in schactivities:
            activities.append(schact.activity)
    context["activities"] = activities
    return render(request, "eighth/choose_activity.html", context)

@eighth_admin_required
def eighth_choose_group(request):
    next = request.GET.get('next', '')

    groups = Group.objects.all().order_by("name")
    return render(request, "eighth/choose_group.html", {
        "page": "eighth_admin",
        "groups": groups,
        "next": "/eighth/{}group/".format(next)
    })

@eighth_admin_required
def eighth_confirm_view(request, action=None, postfields=None):
    if action is None:
        action = "complete this operation"

    if postfields is None:
        postfields = {}

    return render(request, "eighth/confirm.html", {
        "page": "eighth_admin",
        "action": action,
        "postfields": postfields
    })


def signup_student(user, block, activity, force=False):
    """Sign up a student for an eighth period activity.

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
        if current_signup.activity.sticky and not force:
            raise Exception("You are stuck in a stickied activity: {}" \
                .format(current_signup.activity)
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

    grp = Group.objects.get(id=group)
    act = EighthActivity.objects.get(id=activity)
    blk = EighthBlock.objects.get(id=block)
    if 'confirm' in request.POST:
        users = User.objects.filter(groups=grp)

        for user in users:
            signup_student(user, blk, act, True)            



        return redirect("/eighth/admin?success=1")
    else:
        return eighth_confirm_view(request,
            "register {} for {} on {}".format(
                grp.name,
                act.name,
                blk
            )
        )

@eighth_admin_required
def eighth_activities_modify(request, match=None):
    map = unmatch(match)
    activity = map.get('activity')
    next = request.path.split('eighth/')[1]
    if activity is None:
        return redirect("/eighth/choose/activity?add=1&next="+next)

@eighth_admin_required
def eighth_blocks_edit(request, block_id=None):
    if block_id is None:
        blocks = EighthBlock.objects.get_current_blocks()
        return render(request, "eighth/blocks.html", {
            "page": "eighth_admin",
            "blocks": blocks
        })
    elif 'confirm' in request.POST:
        block = EighthBlock.objects.get(id=block_id)
        date = parse_date(request.POST.get('date'))
        if date != block.date:
            block.date = date
        block_letter = request.POST.get('block_letter')
        if block_letter != block.block_letter:
            block.block_letter = block_letter
        block.save()
        return redirect("/eighth/blocks/edit/?success=1")
    else:
        block = EighthBlock.objects.get(id=block_id)
        return render(request, "eighth/block_edit.html", {
            "page": "eighth_admin",
            "block": block
        })

@eighth_admin_required
def eighth_blocks_add(request):
    blockletters = request.POST.getlist('blocks')
    date = request.POST.get('date')

    if 'confirm' in request.POST:
        # Because of multiple checkbox wierdness
        blockletters = request.POST.get('blocks').split(',')
        blocks = []
        dtime = parse_date(date)
        for bl in blockletters:
            if len(EighthBlock.objects.filter(date=dtime, block_letter=list(bl)[0])) < 1:
                EighthBlock.objects.create(
                    date=dtime,
                    block_letter=list(bl)[0]
                )
            else:
                pass
                # The block already existed
        return redirect("/eighth/admin?success=1")
    else:
        blocks = ""
        for bl in blockletters:
            blocks += "<li>{} {} Block</li>".format(date, bl)
        return eighth_confirm_view(request,
            "register the following blocks: <ul>{}</ul>".format(blocks),
            {
                "date": date,
                "blocks": ','.join(blockletters)
            }
        )

@eighth_teacher_required
def eighth_teacher_view(request):
    return render(request, "eighth/teacher.html", {"page": "eighth_teacher"})



@eighth_student_required
def eighth_signup_view(request, block_id=None):

    if 'confirm' in request.POST:
        """Actually sign up"""
        signup = signup_student(
            request.user,
            request.POST.get('bid'),
            request.POST.get('aid')
        )

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


class EighthBlockList(generics.ListAPIView):
    """API endpoint that lists all eighth blocks
    """
    queryset = EighthBlock.objects.all()
    serializer_class = EighthBlockListSerializer


class EighthBlockDetail(views.APIView):
    """API endpoint that shows details for an eighth block
    """
    def get(self, request, pk):
        try:
            block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(pk=pk)
        except EighthBlock.DoesNotExist:
            raise Http404

        serializer = EighthBlockDetailSerializer(block, context={"request": request})
        return Response(serializer.data)


# class EighthActivityList(generics.ListAPIView):
#     """API endpoint that allows viewing a list of eighth activities
#     """
#     queryset = EighthActivity.objects.all()
#     serializer_class = EighthActivityDetailSerializer


class EighthActivityDetail(generics.RetrieveAPIView):
    """API endpoint that shows details of an eighth activity.
    """
    queryset = EighthActivity.objects.all()
    serializer_class = EighthActivityDetailSerializer


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
