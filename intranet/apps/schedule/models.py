# -*- coding: utf-8 -*-

import datetime

from django.db import models
from django.utils import timezone


class Time(models.Model):
    hour = models.IntegerField()
    minute = models.IntegerField()

    def __str__(self):
        minute = "0" + str(self.minute) if self.minute < 10 else self.minute
        return "{}:{}".format(self.hour, minute)

    def str_12_hr(self):
        hour = self.hour if self.hour <= 12 else (self.hour - 12)
        minute = "0" + str(self.minute) if self.minute < 10 else self.minute
        return "{}:{}".format(hour, minute)

    def date_obj(self, date):
        return datetime.datetime(date.year, date.month, date.day, self.hour, self.minute)

    class Meta:
        unique_together = (("hour", "minute"))
        ordering = ("hour", "minute")


class Block(models.Model):
    name = models.CharField(max_length=100)
    start = models.ForeignKey('Time', related_name='blockstart', on_delete=models.CASCADE)
    end = models.ForeignKey('Time', related_name='blockend', on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    def __str__(self):
        return "{}: {} - {}".format(self.name, self.start, self.end)

    class Meta:
        unique_together = (("order", "name", "start", "end"))
        ordering = ("order", "name", "start", "end")


class CodeName(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class DayType(models.Model):
    name = models.CharField(max_length=100)
    codenames = models.ManyToManyField('CodeName', blank=True)
    special = models.BooleanField(default=False)
    blocks = models.ManyToManyField('Block', blank=True)

    def __str__(self):
        return self.name

    @property
    def class_name(self):
        n = self.name.lower()
        t = "other"

        if "blue day" in n or "mod blue" in n:
            t = "blue"

        if "red day" in n or "mod red" in n:
            t = "red"

        if "anchor day" in n or "mod anchor" in n:
            t = "anchor"

        if self.special:
            return "day-type-{} day-special".format(t)
        else:
            return "day-type-{}".format(t)

    @property
    def start_time(self):
        """ Returns Time the school day begins.
            Returns None if there are no blocks.
        """
        if self.no_school:
            return None
        return self.blocks.first().start

    @property
    def end_time(self):
        """ Returns Time the school day ends.
            Returns None if there are no blocks.
        """
        if self.no_school:
            return None
        return self.blocks.last().end

    @property
    def no_school(self):
        """Returns True if no blocks are scheduled."""
        return self.blocks.count() == 0

    class Meta:
        ordering = ("name",)


class DayManager(models.Manager):

    def get_future_days(self):
        """Return only future Day objects."""
        today = timezone.now().date()

        return Day.objects.filter(date__gte=today)

    def today(self):
        """Return the Day for the current day"""
        today = timezone.now().date()
        try:
            return Day.objects.get(date=today)
        except Day.DoesNotExist:
            return None


class Day(models.Model):
    objects = DayManager()
    date = models.DateField(unique=True)
    day_type = models.ForeignKey('DayType', on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000, blank=True)

    @property
    def start_time(self):
        """Return time the school day begins """
        return self.day_type.start_time

    @property
    def end_time(self):
        """Return time the school day ends """
        return self.day_type.end_time

    def __str__(self):
        return "{}: {}".format(str(self.date), self.day_type)

    class Meta:
        ordering = ("date",)
