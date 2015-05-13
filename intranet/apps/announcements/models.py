# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Manager, Q
from django.contrib.auth.models import Group
from ..users.models import User


class AnnouncementManager(Manager):
    def visible_to_user(self, user):
        """Get a list of visible announcements for a given user (usually
        request.user).

        These visible announcements will be those that either have no groups
        assigned to them (and are therefore public) or those in which the
        user is a member.

        """

        return Announcement.objects.filter(Q(groups__in=user.groups.all()) |
                                           Q(groups__isnull=True))


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

    objects = AnnouncementManager()

    title = models.CharField(max_length=127)
    content = models.TextField()
    author = models.CharField(max_length=63)
    user = models.ForeignKey(User, null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    groups = models.ManyToManyField(Group, blank=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ["-added"]
