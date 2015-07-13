# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
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
    author = models.CharField(max_length=63, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    groups = models.ManyToManyField(Group, blank=True)

    expiration_date = models.DateTimeField(auto_now=False, default=datetime(3000, 1, 1))

    def get_author(self):
        return self.author if self.author else self.user.full_name

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ["-added"]


class AnnouncementRequest(models.Model):

    """Represents a request for an announcement.

    Attributes:
        title
            The title of the announcement
        content
            The HTML content of the news post
        notes
            Notes for the person who approves the announcement
        added
            The date the request was added
        updated
            The most recent date the request was updated
        user
            The user who submitted the request
        teachers_requested
            The teachers requested to approve the request
        teachers_approved
            The teachers who have approved the request
        posted
            ForeignKey to Announcement if posted

    """

    title = models.CharField(max_length=127)
    content = models.TextField()
    author = models.CharField(max_length=63, blank=True)

    expiration_date = models.DateTimeField(auto_now=False, default=datetime(3000, 1, 1))
    notes = models.TextField()

    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, null=True, blank=True)
    
    teachers_requested = models.ManyToManyField(User, blank=False, related_name="teachers_requested")
    teachers_approved = models.ManyToManyField(User, blank=True, related_name="teachers_approved")

    posted = models.ForeignKey(Announcement, null=True, blank=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ["-added"]

