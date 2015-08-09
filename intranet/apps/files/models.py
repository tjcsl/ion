# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Manager, Q
from django.contrib.auth.models import Group

class HostManager(Manager):
    def visible_to_user(self, user):
        """Get a list of hosts available to a given user.

           Same logic as Announcements and Events.
        """

        return Host.objects.filter(Q(groups_visible__in=user.groups.all()) |
                                   Q(groups_visible__isnull=True))

class Host(models.Model):
    objects = HostManager()

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32)
    address = models.CharField(max_length=255)
    directory = models.CharField(max_length=255, blank=True)

    windows = models.BooleanField(default=False)
    linux = models.BooleanField(default=False)

    groups_visible = models.ManyToManyField(Group, blank=True)

    def visible_to(self, user):
        if self.groups_visible.count() == 0:
            return True
        return (self in Host.objects.visible_to_user(user))

    def __unicode__(self):
        return "{} ({})".format(self.name, self.code)