# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Group

class Host(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32)
    address = models.CharField(max_length=255)
    directory = models.CharField(max_length=255, blank=True)

    windows = models.BooleanField(default=False)
    linux = models.BooleanField(default=False)

    groups_visible = models.ManyToManyField(Group, blank=True)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.code)