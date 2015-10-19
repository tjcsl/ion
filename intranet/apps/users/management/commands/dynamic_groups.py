# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from intranet import settings
from intranet.apps.users.models import User
from intranet.apps.groups.models import Group


class Command(BaseCommand):
    help = "Update dynamic groups."

    def handle(self, **options):
        """ Create "Class of 20[16-19]" groups """
        for gr in [2016, 2017, 2018, 2019]:
            users = User.objects.filter(username__startswith="{}".format(gr))
            grp, _ = Group.objects.get_or_create(name="Class of {}".format(gr))
            self.stdout.write("{}: {} users".format(gr, users.count()))
            for u in users:
                u.groups.add(grp)
                u.save()
            self.stdout.write("{}: Processed".format(gr))


        self.stdout.write("Done.")