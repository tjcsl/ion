# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User
from intranet.apps.eighth.models import EighthSignup, EighthBlock


class Command(BaseCommand):
    help = "Find duplicate signups in the system that violate the one-signup-per-block constraint."

    def add_arguments(self, parser):
        parser.add_argument('--fix',
                            action='store_true',
                            dest='fix',
                            default=False,
                            help='Fix.')

    def handle(self, *args, **options):

        fix = options["fix"]

        for u in User.objects.all():
            for b in EighthBlock.objects.all():
                su = EighthSignup.objects.filter(user=u, scheduled_activity__block=b)
                if not (su.count() == 0 or su.count() == 1):
                    print("Duplicate: {} {}".format(u.id, b.id))
                    print("Scheduled activities:")
                    print(su)
                    if fix:
                        if su[0].scheduled_activity.both_blocks:
                            sibling = su[0].scheduled_activity.get_both_blocks_sibling()
                            if EighthSignup.objects.filter(user=u, scheduled_activity=sibling).exists():
                                su[1].delete()
                                print("Deleted {}".format(su[1]))