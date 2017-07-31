# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User


# TODO: UserCache
class Command(BaseCommand):
    help = "Set DB cache from LDAP for users"

    def add_arguments(self, parser):
        parser.add_argument('action', action='store', nargs=1, metavar='action: [set, flush]', help="Action to perform [set, flush]")

    def handle(self, **options):
        if options['action'][0] == "flush":
            for user in User.objects.exclude(cache=None):
                user.cache.delete()
            self.stdout.write("Done.")
        elif options['action'][0] == "set":
            for user in User.objects.all():
                if not user.is_active:
                    continue
                if not user.cache:
                    self.stdout.write("Setting DB cache for {}".format(user.username))
                    user.set_cache()
            self.stdout.write("Done.")
        else:
            self.stdout.write("Invalid Action: Choose from [set, flush]")
