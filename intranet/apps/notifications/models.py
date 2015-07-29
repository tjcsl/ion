# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..users.models import User
from django.db import models

class NotificationConfig(models.Model):
    user = models.OneToOneField(User)
    android_gcm_token = models.CharField(max_length=250, blank=True, null=True)
    android_gcm_rand = models.CharField(max_length=100, blank=True, null=True)
    android_gcm_time = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return "{}".format(self.user)