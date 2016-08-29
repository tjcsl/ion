# -*- coding: utf-8 -*-

import sys
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from intranet.apps.users.models import User
from intranet.apps.eighth.models import EighthSignup
from intranet.db.ldap_db import LDAPConnection, LDAPFilter
from django.core.exceptions import ObjectDoesNotExist
class Command(BaseCommand):
    help = "Perform end-of-year cleanup duties."

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', dest='run', default=False, help='Actually run.')

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            print("Abort.")
            sys.exit()

    def chk(self, q, test):
        if test:
            print("OK:", q)
        else:
            print("ERROR:", q)
            print("Abort.")
            sys.exit()

    def handle(self, *args, **options):
        do_run = options["run"]

        if do_run:
            self.ask("===== WARNING! =====\n\n"
                     "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                     "===== WARNING! =====\n\n"
                     "Continue?")
        else:
            print("In pretend mode.")

        current_year = datetime.datetime.now().year
        new_senior_year = current_year + 1
        turnover_date = datetime.datetime(current_year, 7, 1)
        print("Turnover date set to: {}".format(turnover_date.strftime("%c")))

        self.chk("SENIOR_GRADUATION_YEAR = {} in settings/__init__.py".format(new_senior_year),
                 settings.SENIOR_GRADUATION_YEAR == new_senior_year)

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

        print("Resolving absences")
        if do_run:
            self.clear_absences()

        print("Updating welcome state")
        if do_run:
            self.update_welcome()

        print("Deleting graduated users")
        if do_run:
            self.handle_delete()

    def clear_absences(self):
        absents = EighthSignup.objects.filter(was_absent=True)
        print("{} absents".format(absents.count()))
        absents.update(was_absent=True)


    def update_welcome(self):
        User.objects.all().update(seen_welcome=False)

    def handle_delete(self):
        for usr in User.objects.all():
            try:
                name = usr.first_name
            except ObjectDoesNotExist:
                print("User", usr,  "DELETE")
                usr.handle_delete()
                usr.delete()
            else:
                #print("User", usr, "KEEP")
                pass