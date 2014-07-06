from django.shortcuts import redirect, render
from django.http import Http404
from intranet.apps.auth.decorators import eighth_admin_required
from intranet.apps.eighth.models import EighthSponsor
from itertools import chain
from intranet.apps.users.models import User
from .common import eighth_confirm_view
import logging
logger = logging.getLogger(__name__)

@eighth_admin_required
def eighth_activities_sponsors_edit(request, sponsor_id=None):
    if sponsor_id is None:
        sponsors = EighthSponsor.objects.all()
        users = User.objects.all()
        return render(request, "eighth/activity_sponsors.html", {
            "page": "eighth_admin",
            "sponsors": sponsors,
            "users": users
        })
    if 'confirm' in request.POST:
        sp = EighthSponsor.objects.get(id=sponsor_id)
        if 'user' in request.POST:
            sp.user = User.objects.get(id=request.POST.get('user'))
        if 'first_name' in request.POST:
            sp.first_name = request.POST.get('first_name')
        if 'last_name' in request.POST:
            sp.last_name = request.POST.get('last_name')
        sp.online_attendance = ('online_attendance' in request.POST)
        sp.save()
    try:
        sp = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        raise Http404

    return render(request, "eighth/activity_sponsor_edit.html", {
        "page": "eighth_admin",
        "sponsor": sp,
        "users": User.objects.all()
    })

@eighth_admin_required
def eighth_activities_sponsors_add(request):
    if 'confirm' in request.POST:
        user = request.POST.get('user')
        if user is not "" and user is not None:
            try:
                user = User.objects.get(id=user)
            except User.DoesNotExist:
                raise Exception("The user referenced does not exist")
        else:
            user = None
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        online_attendance = ('online_attendance' in request.POST)
        sp = EighthSponsor.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            online_attendance=online_attendance
        )
        return redirect("/eighth/activities/sponsors/edit/{}".format(sp.id))
    else:
        return redirect("/eighth/activities/sponsors/edit")


@eighth_admin_required
def eighth_activities_sponsors_delete(request, sponsor_id):
    try:
        sp = EighthSponsor.objects.get(id=sponsor_id)
    except EighthSponsor.DoesNotExist:
        raise Http404

    if 'confirm' in request.POST:
        sp.delete()
        return redirect("/eighth/activities/sponsors/edit/?success=1")
    else:
        return eighth_confirm_view(request,
            "delete activity sponsor {}".format(sp)
        )
