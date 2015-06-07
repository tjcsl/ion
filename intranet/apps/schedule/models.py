# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import text_type
from django.db import models


class Time(models.Model):
    hour = models.IntegerField()
    minute = models.IntegerField()

    def __unicode__(self):
        minute = "0"+str(self.minute) if self.minute < 10 else self.minute
        return "{}:{}".format(self.hour, minute)

    def str_12_hr(self):
        hour = self.hour if self.hour <= 12 else (self.hour - 12)
        minute = "0"+str(self.minute) if self.minute < 10 else self.minute
        return "{}:{}".format(hour, minute)

    class Meta:
        unique_together = (("hour", "minute"))
        ordering = ("hour", "minute")


class Block(models.Model):
    name = models.CharField(max_length=100)
    start = models.ForeignKey('Time', related_name='blockstart')
    end = models.ForeignKey('Time', related_name='blockend')

    def __unicode__(self):
        return "{}: {}-{}".format(self.name, self.start, self.end)

    class Meta:
        unique_together = (("name", "start", "end"))
        ordering = ("name", "start", "end")


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

    class Meta:
        ordering = ("name",)


class Day(models.Model):
    date = models.DateField(unique=True)
    day_type = models.ForeignKey('DayType')

    def __unicode__(self):
        return "{}: {}".format(text_type(self.date), self.day_type)

    class Meta:
        ordering = ("date",)
