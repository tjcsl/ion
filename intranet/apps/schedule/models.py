# -*- coding: utf-8 -*-

import datetime

from django.db import models


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

    class Meta:
        ordering = ("name",)


class DayManager(models.Manager):

    def get_future_days(self):
        """Return only future Day objects."""
        today = datetime.datetime.now().date()

        return Day.objects.filter(date__gte=today)


class Day(models.Model):
    objects = DayManager()
    date = models.DateField(unique=True)
    day_type = models.ForeignKey('DayType', on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000, blank=True)

    def __str__(self):
        return "{}: {}".format(str(self.date), self.day_type)

    class Meta:
        ordering = ("date",)
