# -*- coding: utf-8 -*-

from django.db import models


class Page(models.Model):
    iframe = models.BooleanField(default=False)
    template = models.CharField(max_length=50, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    button = models.CharField(max_length=30, null=True, blank=True)
    order = models.IntegerField(default=0)


class Sign(models.Model):
    """ name
            A friendly name for the display
        display
            An internal code sent from the display
        status
            One of auto, eighth, schedule, status, url
        eighth_block_increment
            The block_increment if the status is eighth
        url
            The url if the status is url.
    """
    name = models.CharField(max_length=1000)
    display = models.CharField(max_length=100, unique=True)
    eighth_block_increment = models.IntegerField(default=0, null=True, blank=True)
    landscape = models.BooleanField(default=False)
    map_location = models.CharField(max_length=20, null=True, blank=True)

    lock_page = models.ForeignKey(Page,
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  related_name="_unused_1")
    default_page = models.ForeignKey(Page,
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     blank=True,
                                     related_name="_unused_2")
    pages = models.ManyToManyField(Page)

    def __str__(self):
        return "{} ({})".format(self.name, self.display)
