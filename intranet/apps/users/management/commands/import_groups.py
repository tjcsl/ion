# -*- coding: utf-8 -*-

import csv

from django.core.management.base import BaseCommand

from intranet.apps.groups.models import Group
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Import groups from CSV"

    def handle(self, *args, **options):
        mappings = {}
        with open('groups_name.csv', 'r') as namesopen:
            names = csv.reader(namesopen)
            for row in names:
                gid, gname, gdesc = row
                gname = gname.replace("eighth_", "")
                gexist = Group.objects.filter(name=gname)
                if gexist.count() == 1:
                    mappings[gid] = gexist[0]
                else:
                    ngrp = Group.objects.create(name=gname)
                    self.stdout.write("Created group {} with new id {}, old id {}".format(gname, ngrp.id, gid))
                    mappings[gid] = ngrp

        self.stdout.write("{}".format(mappings))
        with open('groups_static.csv', 'r') as staticopen:
            static = csv.reader(staticopen)
            for row in static:
                uid, gid = row
                try:
                    usrobj = User.objects.get(id=uid)
                except User.DoesNotExist:
                    self.stdout.write("UID {} doesn't exist, for adding to group {}".format(uid, gid))
                else:
                    grp = mappings[gid]
                    usrobj.groups.add(grp)
                    usrobj.save()

        self.stdout.write("Done.")
