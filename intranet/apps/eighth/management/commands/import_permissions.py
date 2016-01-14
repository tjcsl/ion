# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthActivity
from intranet.apps.groups.models import Group
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Transfer attendance data"

    def handle(self, **options):
        """
            Exported "eighth_activity_permissions" table in CSV format
        """
        perm_map = {}
        with open('eighth_activity_permissions.csv', 'r') as absperms:
            perms = csv.reader(absperms)
            for row in perms:
                aid, uid = row
                try:
                    usr = User.objects.get(id=uid)
                except User.DoesNotExist:
                    self.stdout.write("User {} doesn't exist, aid {}".format(uid, aid))
                else:
                    if aid in perm_map:
                        perm_map[aid].append(usr)
                    else:
                        perm_map[aid] = [usr]

        for aid in perm_map:
            try:
                act = EighthActivity.objects.get(id=aid)
            except EighthActivity.DoesNotExist:
                self.stdout.write("Activity {} doesn't exist".format(aid))
            else:
                self.stdout.write("{}: {}".format(aid, EighthActivity.objects.get(id=aid)))
                grp, _ = Group.objects.get_or_create(name="{} -- Permissions".format("{}".format(act)[:55]))
                users = perm_map[aid]
                for u in users:
                    u.groups.add(grp)
                    u.save()
                act.groups_allowed.add(grp)
                act.save()

        self.stdout.write("Done.")
