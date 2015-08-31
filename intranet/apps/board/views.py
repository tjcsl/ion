# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from ..auth.decorators import board_admin_required
from ..groups.models import Group
from ..users.models import User, Class
from .models import Board, BoardPost, BoardPostComment

logger = logging.getLogger(__name__)

def home(request):
    """ The homepage, showing all board posts available to you.
    """

    context = {
        "posts": BoardPost.objects.all()
    }

    return render(request, "board/home.html", context)


def class_feed(request, class_id):
    """ The feed of a class.

    """
    class_obj = Class(id=class_id)
    try:
        name = class_obj.name
    except Exception:
        # The class doesn't actually exist
        raise http.Http404

    try:
        board = Board.objects.get(class_id=class_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(class_id=class_id)

    if not board.has_member(request.user):
        raise http.Http403

    context = {
        "board": board,
        "type": "class",
        "class_id": class_id,
        "posts": BoardPost.objects.filter(board__class_id=class_id)
    }

    return render(request, "board/feed.html", context)

def section_feed(request, section_id):
    """ The feed of a section.

    """

    context = {
        "type": "section",
        "section_id": section_id,
        "posts": BoardPost.objects.filter(board__section_id=section_id)
    }

    return render(request, "board/feed.html", context)