import logging
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from .models import EighthBlock, EighthActivity, EighthSignup
from rest_framework import generics, views
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from .serializers import EighthBlockListSerializer, \
    EighthBlockDetailSerializer, EighthActivityDetailSerializer, \
    EighthSignupSerializer
from intranet.apps.auth.decorators import *
logger = logging.getLogger(__name__)


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
    return render(request, "eighth/admin.html", {"page": "eighth_admin"})

@eighth_admin_required
def eighth_choose_block(request):
    next = request.GET.get('next', 'signup')

    blocks = EighthBlock.objects.get_current_blocks()
    return render(request, "eighth/choose_block.html", {
        "page": "eighth_admin",
        "blocks": blocks,
        "next": "/eighth/{}/".format(next)
    })





@login_required
def eighth_teacher_view(request):
    return render(request, "eighth/teacher.html", {"page": "eighth_teacher"})



@login_required
def eighth_signup_view(request, block_id=None):
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

    context = {
        "page": "eighth",
        "user": user,
        "block_info": block_info,
        "activities_list": JSONRenderer().render(block_info["activities"]),
        "active_block": block
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
