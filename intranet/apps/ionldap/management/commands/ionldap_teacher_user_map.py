# -*- coding: utf-8 -*-

import csv

from django.core.management.base import BaseCommand

from intranet.apps.ionldap.models import LDAPCourse
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Add teacher user field to ionldap"

    def handle(self, *args, **options):
        for course in LDAPCourse.objects.all():
            teacher = course.teacher_user_find()
            print(course, teacher)
            if teacher:
                course.teacher_user = teacher
                course.save()