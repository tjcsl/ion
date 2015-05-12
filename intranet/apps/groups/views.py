# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render
from django.http import Http404
# from ..users.models import User
from .forms import GroupForm

logger = logging.getLogger(__name__)


# this is the one that students see
# has add/remove from groups form
# students can only add themselves to non-admin groups unless they are already an admin
@login_required
def groups_view(request):
    return render(request, "groups/groups.html", {
        "all_groups": Group.objects.all(),
        "group_admin": request.user.has_admin_permission("groups")
    })


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
        "form": form,
        "action": "add",
        "success": success
    }
    return render(request, "groups/addmodify.html", context)