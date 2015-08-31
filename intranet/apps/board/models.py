# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q
from ..eighth.models import EighthActivity
from ..groups.models import Group
from ..users.models import User

class Board(models.Model):
    """A Board is a collection of BoardPosts for a specific
       eighth period activity, class, class section, or group.

    """

    # Identifiers
    activity = models.OneToOneField(EighthActivity, null=True)
    class_id = models.CharField(max_length=100, blank=True)
    section_id = models.CharField(max_length=100, blank=True)
    group = models.OneToOneField(DjangoGroup, null=True)

    posts = models.ManyToManyField("BoardPost", null=True)


class BoardPost(models.Model):
    """ A BoardPost is a post by a user in a specific Board.
        They must be in the activity/class/class section/group
        to post to the board.
    """

    title = models.CharField(max_length=250)
    content = models.TextField(max_length=10000)

    user = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    comments = models.ManyToManyField("BoardPostComment", null=True)

class BoardPostComment(models.Model):
    """ A BoardPostComment is a comment on a BoardPost by a user in
        a specific Board.
    """

    content = models.TextField(max_length=1000)
    user = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)