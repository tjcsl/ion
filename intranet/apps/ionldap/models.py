# -*- coding: utf-8 -*-

import logging

from django.db import models

from ..search.views import get_search_results
from ..users.models import User

logger = logging.getLogger(__name__)


class LDAPCourse(models.Model):
    users = models.ManyToManyField(User)

    course_id = models.CharField(max_length=10, blank=False, unique=False)
    section_id = models.CharField(max_length=10, blank=False, unique=True)

    course_title = models.CharField(max_length=100, blank=True)
    course_short_title = models.CharField(max_length=100, blank=True)
    teacher_name = models.CharField(max_length=100, blank=True)
    teacher_user = models.ForeignKey(User, null=True, related_name="ionldap_course_teacher", on_delete=models.CASCADE)
    room_name = models.CharField(max_length=100, blank=True)
    term_code = models.CharField(max_length=10, blank=True)
    period = models.IntegerField()
    end_period = models.IntegerField()

    @property
    def teacher(self):
        return self.teacher_user.last_name if self.teacher_user else self.teacher_name

    @property
    def periods(self):
        return "{}".format(self.period) + ("-{}".format(self.end_period) if self.end_period and self.end_period != self.period else "")

    def teacher_user_find(self):
        query = self.teacher_name.replace(",", "")  # Remove comma between last and first
        query = " ".join(query.split(" ")[:2])  # Remove middle initial
        try:
            query_error, users = get_search_results(query, False)
        except Exception:
            return None

        logger.debug("user find result: {}".format(users))

        if users and len(users) == 1:
            return users[0]
        else:
            # Last name and staff check only
            query = "{} grade:staff".format(self.teacher_name.split(", ", 1)[0])
            try:
                query_error, users = get_search_results(query, False)
            except Exception:
                return None

            logger.debug("user find2 result: {}".format(users))

            if users and len(users) == 1:
                return users[0]

    def __str__(self):
        return "{} - {} Period {}".format(self.course_title, self.teacher, self.periods)

    class Meta:
        ordering = ("period", "end_period")
