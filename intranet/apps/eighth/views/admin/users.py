# -*- coding: utf-8 -*-

import logging

from django.http import Http404
from django.shortcuts import render, get_object_or_404

from ....auth.decorators import eighth_admin_required
from ....users.models import User

logger = logging.getLogger(__name__)


@eighth_admin_required
def list_user_view(request):
    users = User.objects.all()
    return render(request, 'eighth/admin/list_users.html', {'users': users})


@eighth_admin_required
def delete_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        raise Http404
    else:
        return render(request, 'eighth/admin/delete_user.html', {'user': user})


@eighth_admin_required
def add_user_view(request):
    """Add a new user"""
    if request.method == 'POST':
        pass
