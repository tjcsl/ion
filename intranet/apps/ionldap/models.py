# -*- coding: utf-8 -*-
from django.db import models

from ..users.models import User


class LDAPCourse(models.Model):
    users = models.ManyToManyField(User)

    course_id = models.CharField(max_length=10, blank=False, unique=False)
    section_id = models.CharField(max_length=10, blank=False, unique=True)

    course_title = models.CharField(max_length=100, blank=True)
    course_short_title = models.CharField(max_length=100, blank=True)
    teacher_name = models.CharField(max_length=100, blank=True)
    room_name = models.CharField(max_length=100, blank=True)
    term_code = models.CharField(max_length=10, blank=True)
    period = models.IntegerField()
    end_period = models.IntegerField()

    def __str__(self):
        return "{} - {} ({})".format(self.course_title, self.teacher_name, self.section_id)
