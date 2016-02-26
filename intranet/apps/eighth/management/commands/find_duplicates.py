# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthBlock, EighthSignup
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Find duplicate signups in the system that violate the one-signup-per-block constraint."

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', dest='fix', default=False, help='Fix.')

    def handle(self, *args, **options):

        fix = options["fix"]
        found = False

        for u in User.objects.all():
            for b in EighthBlock.objects.all():
                su = EighthSignup.objects.filter(user=u, scheduled_activity__block=b)
                if su.count() != 0 and su.count() != 1:
                    found = True
                    print("Duplicate: {} {}".format(u.id, b.id))
                    print("Scheduled activities:", su)
                    if fix:
                        if su[0].scheduled_activity.activity.both_blocks:
                            sibling = su[0].scheduled_activity.get_both_blocks_sibling()
                            if EighthSignup.objects.filter(user=u, scheduled_activity=sibling).exists():
                                print("Deleted su1 {}".format(su[1]))
                                su[1].delete()
                        elif su[1].scheduled_activity.activity.both_blocks:
                            sibling = su[1].scheduled_activity.get_both_blocks_sibling()
                            if EighthSignup.objects.filter(user=u, scheduled_activity=sibling).exists():
                                print("Deleted su0 {}".format(su[0]))
                                su[0].delete()
        if not found:
            print("No duplicate signups found.")
