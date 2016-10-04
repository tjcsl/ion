# -*- coding: utf-8 -*-
import sys

from django.core.management.base import BaseCommand
from django.db.models.deletion import Collector

from intranet.apps.users.models import User

teststaff = User.get_user(id=7011)


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
            except User.DoesNotExist:
            c = Collector(using="default")
            c.collect([user])
            objects = c.instances_with_model()
            for obj in list(objects)[1:]:
                if not obj[1].__str__() == "User_groups object" and obj[0] is not User:
                    if options['run']:
                        try:
                            self.stdout.write("Setting %s user to %s" % (obj[1], teststaff))
                            obj[1].user = teststaff
                            obj[1].save()
                            self.stdout.write("Set %s's user to %s" % (obj[1], teststaff))
                        except:
                            self.stdout.write("DELETE %s" % obj[1])
                    else:
                        self.stdout.write("Would set %s's user to %s" % (obj[1], teststaff))
                else:
                    self.stdout.write("Deleting group relation %s" % obj[1].group)
                    if options['run']:
                        obj[1].delete()
            if options['run']:
                self.stdout.write("===== DELETING USER %s =========" % user)
                user.delete()
            else:
                self.stdout.write("DELETE %s" % user)
