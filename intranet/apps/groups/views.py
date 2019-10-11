import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..auth.decorators import admin_required, deny_restricted
from .forms import GroupForm
from .models import Group

logger = logging.getLogger(__name__)


# this is the one that students see
# has add/remove from groups form
# students can only add themselves to non-admin groups unless they are already an admin
@login_required
@deny_restricted
def groups_view(request):
    group_admin = request.user.has_admin_permission("groups")
    if group_admin and "user" in request.GET:
        user = get_user_model().objects.get(id=request.GET.get("user"))
    else:
        user = request.user
    return render(request, "groups/groups.html", {"user": user, "all_groups": Group.objects.all(), "group_admin": group_admin})


# Create individual views for each form action
@admin_required("groups")
@deny_restricted
def add_group_view(request):
    success = False
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = GroupForm()

    context = {"form": form, "action": "add", "success": success}
    return render(request, "groups/addmodify.html", context)
