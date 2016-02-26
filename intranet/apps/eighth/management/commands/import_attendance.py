# -*- coding: utf-8 -*-

import csv

from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import (EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup)
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Transfer attendance data"

    def handle(self, **options):
        """Exported "eighth_absentees" table in CSV format."""

        with open('eighth_absentees.csv', 'r') as absopen:
            absences = csv.reader(absopen)
            for row in absences:
                bid, uid = row
                try:
                    usr = User.objects.get(id=uid)
                except User.DoesNotExist:
                    self.stdout.write("User {} doesn't exist, bid {}".format(usr, bid))
                else:
                    try:
                        blk = EighthBlock.objects.get(id=bid)
                    except EighthBlock.DoesNotExist:
                        self.stdout.write("Block {} doesn't exist, with user {}".format(bid, uid))
                    else:
                        usr_signup = EighthSignup.objects.filter(user=usr, scheduled_activity__block=blk)
                        self.stdout.write("{} signup: {}".format(usr, usr_signup))
                        if usr_signup.count() == 0:
                            other_abs_act, _ = EighthActivity.objects.get_or_create(name="z-OTHER ABSENCE (transferred from Iodine)",
                                                                                    administrative=True)
                            other_abs_sch, _ = EighthScheduledActivity.objects.get_or_create(block=blk, activity=other_abs_act)
                            other_abs_su = EighthSignup.objects.create(user=usr, scheduled_activity=other_abs_sch, was_absent=True)
                            self.stdout.write("{} Signup on {} created: {}".format(usr, bid, other_abs_su))
                        else:
                            s = usr_signup[0]
                            s.was_absent = True
                            s.save()
                            sa = s.scheduled_activity
                            sa.attendance_taken = True
                            sa.save()
                            self.stdout.write("{} Signup on {} modified: {}".format(usr, bid, usr_signup[0]))

        self.stdout.write("Done.")
