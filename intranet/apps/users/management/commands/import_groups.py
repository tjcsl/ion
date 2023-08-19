import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from intranet.apps.groups.models import Group


class Command(BaseCommand):
    help = "Import groups from CSV"

    def handle(self, *args, **options):
        mappings = {}
        with open("groups_name.csv", "r", encoding="utf-8") as namesopen:
            names = csv.reader(namesopen)
            for gid, gname, _ in names:
                gname = gname.replace("eighth_", "")
                gexist = Group.objects.filter(name=gname)
                if gexist.count() == 1:
                    mappings[gid] = gexist[0]
                else:
                    ngrp = Group.objects.create(name=gname)
                    self.stdout.write(f"Created group {gname} with new id {ngrp.id}, old id {gid}")
                    mappings[gid] = ngrp

        self.stdout.write(f"{mappings}")
        with open("groups_static.csv", "r", encoding="utf-8") as staticopen:
            static = csv.reader(staticopen)
            for uid, gid in static:
                try:
                    usrobj = get_user_model().objects.get(id=uid)
                except get_user_model().DoesNotExist:
                    self.stdout.write(f"UID {uid} doesn't exist, for adding to group {gid}")
                else:
                    grp = mappings[gid]
                    usrobj.groups.add(grp)
                    usrobj.save()

        self.stdout.write("Done.")
