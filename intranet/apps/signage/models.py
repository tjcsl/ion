# -*- coding: utf-8 -*-

from django.db import models


class Sign(models.Model):
    """
    name
        A friendly name for the display
    display
        An internal code sent from the display
    status
        One of auto, eighth, schedule, status, url
    eighth_block_increment
        The block_increment if the status is eighth
    url
        The url if the status is url
    """
    name = models.CharField(max_length=1000)
    display = models.CharField(max_length=100, unique=True)
    STATUSES = (
        ("auto", "Auto - Schedule/Eighth"),
        ("autourl", "Auto - URL/Eighth"),
        ("eighth", "Eighth Period"),
        ("schedule", "Bell Schedule"),
        ("status", "Schedule/Clock"),
        ("url", "Custom URL")
    )
    use_frameset = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUSES, default="auto")
    eighth_block_increment = models.IntegerField(default=0, null=True, blank=True)
    url = models.CharField(max_length=2000, null=True, blank=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.display)
