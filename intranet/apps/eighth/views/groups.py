from django.http import Http404
from django.shortcuts import redirect, render
from django.contrib.auth.models import Group
from intranet.apps.auth.decorators import eighth_admin_required
import logging
logger = logging.getLogger(__name__)

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
def eighth_groups_edit(request, group_id=None):
    if group_id is None:
        return render(request, "eighth/groups.html", {
            "groups": Group.objects.all()
        })
    elif 'confirm' in request.POST:
        try:
            gr = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise Http404
        if 'name' in request.POST:
            gr.name = request.POST.get('name')
        if 'remove_member' in request.POST:
            rem = request.POST.getlist('remove_member')
            for member in rem:
                User.objects.get(id=member).groups.remove(gr)
        if 'add_member' in request.POST:
            add = request.POST.getlist('add_member')
            for member in add:
                User.objects.get(id=member).groups.add(gr)
        gr.save()
        return redirect("/eighth/groups/")
    else:
        return render(request, "eighth/group_edit.html", {
            "group": Group.objects.get(id=group_id),
            "members": User.objects.filter(groups__id=group_id)
        })


