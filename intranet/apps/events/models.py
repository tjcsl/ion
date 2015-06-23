# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..users.models import User
from ..eighth.models import EighthScheduledActivity
from ..announcements.models import Announcement
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Manager, Q

class Link(models.Model):
    """A link about an item (Facebook event link, etc).
    """
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=100)

class EventManager(Manager):
    def visible_to_user(self, user):
        """Get a list of visible events for a given user (usually
        request.user).

        These visible events will be those that either have no groups
        assigned to them (and are therefore public) or those in which the
        user is a member.

        """

        return Event.objects.filter(Q(groups__in=user.groups.all()) |
                                    Q(groups__isnull=True) |
                                    Q(user=user))

class Event(models.Model):
    """An event available to the TJ community.
    """
    objects = EventManager()

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)
    links = models.ManyToManyField("Link")
    created_time = models.DateTimeField(auto_now=True)
    last_modified_time = models.DateTimeField(auto_now_add=True)

    time = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=100)
    user = models.ForeignKey(User)

    scheduled_activity = models.ForeignKey(EighthScheduledActivity, null=True)
    announcement = models.ForeignKey(Announcement, null=True)
    
    groups = models.ManyToManyField(Group, blank=True)