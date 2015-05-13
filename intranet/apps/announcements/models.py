# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Group
from ..users.models import User

class Announcement(models.Model):

    """Represents an announcement.

    Attributes:
        title
            The title of the announcement
        content
            The HTML content of the news post
        authors
            The name of the author
        added
            The date the announcement was added
        updated
            The most recent date the announcement was updated

    """
    title = models.CharField(max_length=127)
    content = models.TextField()
    author = models.CharField(max_length=63)
    user = models.ForeignKey(User, null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    groups = models.ManyToManyField(Group, blank=True)

    def __unicode__(self):
        return self.title
