# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import text_type
from django.db import models


class Time(models.Model):
    hour = models.IntegerField()
    min = models.IntegerField()

    def __unicode__(self):
        return "{}:{}".format(self.hour % 12, "0"+str(self.min) if self.min < 10 else self.min)

    class Meta:
        unique_together = (("hour", "min"))
        ordering = ("hour", "min")


class Block(models.Model):
    name = models.CharField(max_length=100)
    start = models.ForeignKey('Time', related_name='blockstart')
    end = models.ForeignKey('Time', related_name='blockend')

    def __unicode__(self):
        return "{}: {}-{}".format(self.name, self.start, self.end)

    class Meta:
        unique_together = (("name", "start", "end"))


class CodeName(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class DayType(models.Model):
    name = models.CharField(max_length=100)
    codenames = models.ManyToManyField('CodeName', blank=True)
    special = models.BooleanField(default=False)
    blocks = models.ManyToManyField('Block', blank=True)

    def __unicode__(self):
        return self.name


class Day(models.Model):
    date = models.DateField(unique=True)
    type = models.ForeignKey('DayType')

    def __unicode__(self):
        return "{}: {}".format(text_type(self.date), self.type)
