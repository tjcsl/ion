""" Activities """
from django.shortcuts import redirect, render
from django.http import Http404
from intranet.apps.auth.decorators import eighth_admin_required
from intranet.apps.eighth.models import EighthActivity, EighthSponsor, EighthRoom, EighthScheduledActivity, EighthBlock
from intranet.apps.eighth.serializers import EighthActivityDetailSerializer
from itertools import chain
from rest_framework import generics, views
from .common import get_startdate_fallback, eighth_confirm_view, unmatch
import logging
logger = logging.getLogger(__name__)

def activities_findopenids():
    """
        Finds open IDs for when creating a new activity
        with a custom ID (to prevent creating an activity
        with an ID that already exists).

    """
    acts = EighthActivity.objects.all()
    free = range(1, 2999)
    for act in acts:
        free.remove(act.id)
    return free

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
def eighth_activities_edit(request, activity_id=None):
    if activity_id is None:
        activities = EighthActivity.objects.all()
        return render(request, "eighth/activities.html", {
            "page": "eighth_admin",
            "activities": activities,
            "ids": activities_findopenids()
        })
    if 'confirm' in request.POST:
        act = EighthActivity.objects.get(id=activity_id)
        if 'name' in request.POST:
            act.name = request.POST.get('name')
        if 'description' in request.POST:
            act.description = request.POST.get('description')
        if 'sponsors' in request.POST:
            sponsors = request.POST.getlist('sponsors')
            for sponsor in act.sponsors.all():
                act.sponsors.remove(sponsor)
            for sponsor in sponsors:
                sp = EighthSponsor.objects.get(id=sponsor)
                if sp not in act.sponsors.all():
                    act.sponsors.add(sp)
            
        if 'rooms' in request.POST:
            rooms = request.POST.getlist('rooms')
            for room in act.rooms.all():
                act.rooms.remove(room)
            for room in rooms:
                rm = EighthRoom.objects.get(id=room)
                if rm not in act.rooms.all():
                    act.rooms.add(rm)
        act.restricted = ('restricted' in request.POST)
        act.presign = ('presign' in request.POST)
        act.one_a_day = ('one_a_day' in request.POST)
        act.both_blocks = ('both_blocks' in request.POST)
        act.sticky = ('sticky' in request.POST)
        act.special = ('special' in request.POST)
        
        #for i in ('restricted','presign','one_a_day','both_blocks','sticky','special'):
        #    if i in request.POST:
        #        setattr(act, i, (request.POST.get(i) is '1'))
        #    else:
        #        setattr(act, i, False)
        act.save()
    try:
        activity = EighthActivity.objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        raise Http404

    return render(request, "eighth/activity_edit.html", {
        "page": "eighth_admin",
        "actobj": activity,
        "sponsors": EighthSponsor.objects.all(),
        "rooms": EighthRoom.objects.all()
    })


@eighth_admin_required
def eighth_activities_add(request):
    if 'confirm' in request.POST:
        name = request.POST.get('name')
        desc = request.POST.get('description')
        if desc is None:
            desc = ""
        if 'id' in request.POST and request.POST.get('id') is not "auto":
            try:
                idfilter = EighthActivity.objects.filter(id=int(request.POST.get('id')))
                if len(idfilter) < 1:
                    # ID is good
                    ea = EighthActivity.objects.create(
                        id=request.POST.get('id'),
                        name=name,
                        description=desc
                    )
                    return redirect("/eighth/activities/edit/{}".format(ea.id))
            except ValueError:
                pass
        ea = EighthActivity.objects.create(
            name=name,
            description=desc
        )
        return redirect("/eighth/activities/edit/{}".format(ea.id))
    else:
        return redirect("/eighth/activities/edit")


@eighth_admin_required
def eighth_activities_delete(request, activity_id):
    try:
        act = EighthActivity.objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        raise Http404

    if 'confirm' in request.POST:
        act.delete()
        return redirect("/eighth/activities/edit/?success=1")
    else:
        return eighth_confirm_view(request,
            "delete activity {}".format(act.name)
        )

@eighth_admin_required
def eighth_activities_schedule(request, match=None):
    req = unmatch(match)
    activity = req.get('activity')
    if activity is None:
        return redirect("/eighth/choose/activity?next=activities/schedule/")
    if 'confirm' in request.POST:
        pass
    sd = get_startdate_fallback(request)
    schacts = EighthScheduledActivity.objects.filter(
        activity__id=activity,
        block__date__gt=sd
    )
    blocks = EighthBlock.objects.filter(
        date__gt=sd
    )
    schblocks = []
    for block in blocks:
        sa = schacts.filter(block__id=block.id)
        schblocks.append({
            "block": block,
            "schact": sa[0] if sa else None
        })
    logger.debug(schblocks)
    return render(request, "eighth/activity_schedule.html", {
        "schblocks": schblocks
    })

@eighth_admin_required
def eighth_activities_schedule_form(request):
    if 'activity' in request.GET:
        return redirect("/eighth/activities/schedule/activity/{}".format(request.GET.get('activity')))
    else:
        raise Http404

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


