# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Set DB cache from LDAP for users"

    def add_arguments(self, parser):
        parser.add_argument('--override', action='store_true', dest='override', default=False, help='Clear and set cache for all users')

    def handle(self, **options):
        for user in User.objects.all():
            if options['override']:
                if user.cache:
                    user.cache.delete()
            if not user.cache:
                self.stdout.write("Setting DB cache for {}".format(user.username))
        self.stdout.write("Done.")
