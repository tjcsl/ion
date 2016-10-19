# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User, UserCache


class Command(BaseCommand):
    help = "Set DB cache from LDAP for users"

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', dest='flush', default=False, help="Flush all cache objects")

    def handle(self, **options):
        if options['flush']:
            UserCache.objects.all().delete()
            for user in User.objects.exclude(cache=None):
                user.cache.delete()
            return
        for user in User.objects.all():
            if not user.is_active:
                continue
            if not user.cache:
                self.stdout.write("Setting DB cache for {}".format(user.username))
                user.set_cache()
        self.stdout.write("Done.")
