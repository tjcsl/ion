# -*- coding: utf-8 -*-
import sys

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Delete all users not in LDAP and change their historical data to User with ID 7011"

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', dest='run', default=False, help='Run.')
        parser.add_argument('--confirm', action='store_true', dest='confirm', default=False, help='Skip confirmation.')

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            self.stdout.write("Abort.")
            sys.exit()

    def handle(self, *args, **options):
        if options['run']:
            if not options["confirm"]:
                self.ask("===== WARNING! =====\n\n"
                         "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                         "===== WARNING! =====\n\n"
                         "Continue?")
        for user in User.objects.all():
            try:
                user.first_name
            except ObjectDoesNotExist:
                if options['run']:
                    self.stdout.write("==== DELETING USER %s ====" % user)
                    user.delete()
                else:
                    self.stdout.write("DELETE %s" % user)
            else:
                pass
