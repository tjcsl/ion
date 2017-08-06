# -*- coding: utf-8 -*-

import sys
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from intranet.apps.users.models import User
from intranet.apps.eighth.models import EighthSignup
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = "Perform end-of-year cleanup duties."

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', dest='run', default=False, help='Actually run.')
        parser.add_argument('--confirm', action='store_true', dest='confirm', default=False, help='Skip confirmation.')

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            self.stdout.write("Abort.")
            sys.exit()

    def chk(self, q, test):
        if test:
            self.stdout.write("OK: %s" % q)
        else:
            self.stdout.write("ERROR: %s" % q)
            self.stdout.write("Abort.")
            sys.exit()

    def handle(self, *args, **options):
        do_run = options["run"]

        if do_run:
            if not options["confirm"]:
                self.ask("===== WARNING! =====\n\n"
                         "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                         "===== WARNING! =====\n\n"
                         "Continue?")
        else:
            self.stdout.write("In pretend mode.")

        current_year = datetime.datetime.now().year
        new_senior_year = current_year + 1
        turnover_date = datetime.datetime(current_year, 7, 1)
        self.stdout.write("Turnover date set to: {}".format(turnover_date.strftime("%c")))

        self.chk("SENIOR_GRADUATION_YEAR = {} in settings/__init__.py".format(new_senior_year), settings.SENIOR_GRADUATION_YEAR == new_senior_year)

        """
        EIGHTH:
            EighthBlock: filtered
            EighthSignup: absences removed
            EighthActivity: keep

        ANNOUNCEMENTS:
            AnnouncementRequest: filtered

        USERS:
            User: graduated students deleted
        """

        self.stdout.write("Resolving absences")
        if do_run:
            self.clear_absences()

        self.stdout.write("Updating welcome state")
        if do_run:
            self.update_welcome()

        self.stdout.write("Deleting graduated users")
        if do_run:
            self.handle_delete()

    def clear_absences(self):
        absents = EighthSignup.objects.filter(was_absent=True)
        self.stdout.write("{} absent eighth signups".format(absents.count()))
        for a in absents:
            a.archive_remove_absence()
        self.stdout.write("Archived absences")

    def update_welcome(self):
        User.objects.all().update(seen_welcome=False)

    def handle_delete(self):
        for usr in User.objects.all(graduation_year=datetime.datetime.now().year):
            if not usr.is_superuser and not usr.is_staff:
                usr.handle_delete()
                self.stdout.write(usr.delete())
            else:
                self.stdout.write("User {} KEEP".format(usr.username))
