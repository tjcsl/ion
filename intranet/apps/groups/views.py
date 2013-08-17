import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from intranet.apps.users.models import User
from intranet.decorators import authorized_required
from .models import Group
from .forms import GroupForm

logger = logging.getLogger(__name__)


@login_required
@authorized_required("groups")
def groups_view(request, action=None, id=None, useraction=None, groupid=None):
    success = False
    if request.method == 'POST':
        if action == "add":
            form = GroupForm(request.POST)
        elif action == "modify":
            group = Group.objects.get(id=id)
            form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            success = True
    elif action == "add":
        form = GroupForm()
    elif action == "modify":
        group = Group.objects.get(id=id)
        form = GroupForm(instance=group)
    elif action == "delete":
        group = Group.objects.get(id=id).delete()
        return render(request, "groups/deleted.html", {"user": request.user})
    elif action == "user":
        successful_user_modify = False
        user = request.user
        groups = user.groups
        #othergroups = [i for i in Group.objects.order_by("name").all() if i not in groups]
        if useraction == "add":
            group = Group.objects.get(id=groupid)
            user.usergroups.add(group)
            user.save()
            groups = user.groups
            successful_user_modify = True
        elif useraction == "remove":
            group = Group.objects.get(id=groupid)
            user.usergroups.remove(group)
            user.save()
            groups = user.groups
            successful_user_modify = True
        othergroups = Group.objects.order_by("name").exclude(id__in=[i.id for i in groups])
        return render(request, "groups/usermanage.html", {"user": request.user, "groups": groups, "othergroups": othergroups, "success": successful_user_modify})
    elif action == None:
        return render(request, "groups/view.html", {"user": request.user})
    return render(request, 'groups/addmodify.html', {"user": request.user, "form": form, "action": action, "id": id, "success": success})
