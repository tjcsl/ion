# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q
from ..groups.models import Group

"""
    Sample TJ configuration:

        Host.objects.create(name="Computer Systems Lab",
                            code="csl",
                            address="remote.tjhsst.edu",
                            linux=True)

        afs = Host.objects.create(name="CSL AFS Root",
                                  code="afs",
                                  address="remote.tjhsst.edu",
                                  directory="/afs/csl/",
                                  linux=True)

        afs.groups.add(Group.objects.get(name="admin_all"))

        Host.objects.create(name="Home Folder (M)",
                            code="tj03_m",
                            address="tj03.local.tjhsst.edu",
                            directory="{win}",
                            windows=True)

        Host.objects.create(name="Resources Drive (R)",
                            code="tj03_r",
                            address="tj03.local.tjhsst.edu",
                            directory="/R/",
                            windows=True)
        
        Host.objects.create(name="Windows Root",
                            code="win",
                            address="tj03.local.tjhsst.edu",
                            windows=True)
        
"""


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

    groups_visible = models.ManyToManyField(DjangoGroup, blank=True)

    def visible_to(self, user):
        if self.groups_visible.count() == 0:
            return True
        return (self in Host.objects.visible_to_user(user))

    def __unicode__(self):
        return "{} ({})".format(self.name, self.code)

    class Meta:
        ordering = ["-linux", "name"]
