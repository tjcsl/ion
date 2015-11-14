# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from intranet.apps.eighth.models import EighthBlock, EighthSignup
from intranet.apps.eighth.notifications import absence_email
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Notify users who have an Eighth Period absence."

    def add_arguments(self, parser):
        parser.add_argument('--silent',
                            action='store_true',
                            dest='silent',
                            default=False,
                            help='Be silent.')

        parser.add_argument('--pretend',
                            action='store_true',
                            dest='pretend',
                            default=False,
                            help="Pretend, and don't actually do anything.")

    def handle(self, *args, **options):

        log = not options["silent"]

        absences = EighthSignup.objects.get_absences().filter(absence_emailed=False).nocache()


        for signup in absences:
            if log:
                self.stdout.write("{}".format(signup))
                user = signup.user
            if not options["pretend"]:
                absence_email(signup)
                signup.absence_emailed = True
                signup.save()

        if log:
            self.stdout.write("Done.")
