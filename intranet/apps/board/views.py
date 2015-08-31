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
from ..users.models import User
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

    context = {
        "type": "class",
        "class_id": class_id,
        "posts": BoardPost.objects.filter(board__class_id=class_id)
    }

    return render(requets, "board/feed.html", context)

def class_feed(request, section_id):
    """ The feed of a section.

    """

    context = {
        "type": "section",
        "section_id": section_id,
        "posts": BoardPost.objects.filter(board__section_id=section_id)
    }

    return render(requets, "board/feed.html", context)