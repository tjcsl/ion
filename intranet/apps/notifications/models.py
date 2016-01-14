# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import json

from django.db import models

from ..users.models import User


class NotificationConfig(models.Model):
    user = models.OneToOneField(User)
    gcm_token = models.CharField(max_length=250, blank=True, null=True)
    gcm_time = models.DateTimeField(blank=True, null=True)
    gcm_optout = models.BooleanField(default=False)

    android_gcm_rand = models.CharField(max_length=100, blank=True, null=True)

    @property
    def gcm_token_sha256(self):
        return hashlib.sha256(self.gcm_token.encode()).hexdigest()

    def __str__(self):
        return "{}".format(self.user)


class GCMNotification(models.Model):
    multicast_id = models.CharField(max_length=250)
    num_success = models.IntegerField(default=0)
    num_failure = models.IntegerField(default=0)
    sent_data = models.CharField(max_length=10000)
    sent_to = models.ManyToManyField(NotificationConfig)
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)

    def __str__(self):
        return "{} at {}".format(self.multicast_id, self.time)

    @property
    def data(self):
        json_data = json.loads(self.sent_data)
        if json_data and "data" in json_data:
            return json_data["data"]
        return {}
