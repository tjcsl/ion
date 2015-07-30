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

class GCMNotification(models.Model):
    multicast_id = models.CharField(max_length=250)
    num_success = models.IntegerField(default=0)
    num_failure = models.IntegerField(default=0)
    sent_data = models.CharField(max_length=10000)
    sent_to = models.ManyToManyField(NotificationConfig)
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)