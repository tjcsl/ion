# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from intranet import settings
from intranet.apps.users.models import User
from intranet.apps.groups.models import Group


class Command(BaseCommand):
    help = "Update dynamic groups, and ensure that all students have an entry in the database."

    def handle(self, **options):
        """ Create "Class of 20[16-19]" groups """

        students_grp, _ = Group.objects.get_or_create(name="Students")
        sg_prop = students_grp.properties
        sg_prop.student_visible = True
        sg_prop.save()
        students_grp.save()

        for gr in [2016, 2017, 2018, 2019]:
            users = User.objects.users_in_year(gr)
            grp, _ = Group.objects.get_or_create(name="Class of {}".format(gr))
            grp_prop = grp.properties
            grp_prop.student_visible = True
            grp_prop.save()
            grp.save()
            self.stdout.write("{}: {} users".format(gr, len(users)))
            for u in users:
                u.groups.add(grp)
                u.groups.add(students_grp)
                u.save()
            self.stdout.write("{}: Processed".format(gr))


        self.stdout.write("Done.")