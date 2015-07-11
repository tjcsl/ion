# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..users.models import User
from ..eighth.models import EighthScheduledActivity
from ..announcements.models import Announcement
from datetime import datetime
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
    description = models.TextField(max_length=10000)
    links = models.ManyToManyField("Link", blank=True)
    created_time = models.DateTimeField(auto_now=True)
    last_modified_time = models.DateTimeField(auto_now_add=True)

    time = models.DateTimeField()
    location = models.CharField(max_length=100)
    user = models.ForeignKey(User)

    scheduled_activity = models.ForeignKey(EighthScheduledActivity, null=True, blank=True)
    announcement = models.ForeignKey(Announcement, null=True, blank=True)
    
    groups = models.ManyToManyField(Group, blank=True)

    attending = models.ManyToManyField(User, blank=True, related_name="attending")

    def show_fuzzy_date(self):
        """
        Return whether the event is in the next or previous 2 weeks.
        Determines whether to display the fuzzy date.

        """
        date = self.time.replace(tzinfo=None)
        if date <= datetime.now():
            diff = datetime.now() - date
            if diff.days >= 14:
                return False
        else:
            diff = date - datetime.now()
            if diff.days >= 14:
                return False

        return True




    def __unicode__(self):
        return "{} - {}".format(self.title, self.time)