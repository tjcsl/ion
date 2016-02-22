# -*- coding: utf-8 -*-

import logging
from django.db import models

from ..users.models import User
from ..search.views import get_search_results

logger = logging.getLogger(__name__)


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

    def teacher_user(self):
        try:
            query_error, users = get_search_results(self.teacher_name.replace(",", ""), False)
        except Exception:
            return None

        logger.debug("user find result: {}".format(users))

        if users and len(users) == 1:
            return users[0]

    def __str__(self):
        return "{} - {} ({})".format(self.course_title, self.teacher_name, self.section_id)
