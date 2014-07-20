import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render
from django.http import HttpResponse
from ..users.models import User
from .forms import GroupForm

logger = logging.getLogger(__name__)


# this is the one that students see
# has add/remove from groups form
# students can only add themselves to non-admin groups unless they are already an admin
@login_required
def groups_view(request):
    context = {"page": "groups"}
    return render(request, "groups/groups.html", context)

# Create individual views for each form action
@login_required
def add_group_view(request):
    success = False
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
	    form.save()
	    success = True
    else:
        form = GroupForm()

    context = {
        "page": "groups",
	    "form": form,
	    "action": "add",
	    "success": success
	}
    return render(request, "groups/addmodify.html", context)

# success = False
# if request.method == 'POST':
#     if action == "add":
#         form = GroupForm(request.POST)
#     elif action == "modify":
#         group = Group.objects.get(id=id)
#         form = GroupForm(request.POST, instance=group)
#     if form.is_valid():
#         form.save()
#         success = True
# elif action == "add":
#     form = GroupForm()
# elif action == "modify":
#     group = Group.objects.get(id=id)
#     form = GroupForm(instance=group)
# elif action == "delete":
#     group = Group.objects.get(id=id).delete()
#     return render(request, "groups/deleted.html", {"user": request.user})
# elif action == "user":
#     successful_user_modify = False
#     user = request.user
#     groups = user.groups
#     #othergroups = [i for i in Group.objects.order_by("name").all() if i not in groups]
#     if useraction == "add":
#         group = Group.objects.get(id=groupid)
#         user.usergroups.add(group)
#         user.save()
#         groups = user.groups
#         successful_user_modify = True
#     elif useraction == "remove":
#         group = Group.objects.get(id=groupid)
#         user.usergroups.remove(group)
#         user.save()
#         groups = user.groups
#         successful_user_modify = True
#     othergroups = Group.objects.order_by("name").exclude(id__in=[i.id for i in groups])
#     return render(request, "groups/usermanage.html", {"user": request.user, "groups": groups, "othergroups": othergroups, "success": successful_user_modify})
# elif action == None:
#     return render(request, "groups/view.html", {"user": request.user})
# return render(request, 'groups/addmodify.html', {"user": request.user, "form": form, "action": action, "id": id, "success": success})
