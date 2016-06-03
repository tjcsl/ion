# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Lock account"
    args="<u>"

    def handle(self, *args, **options):
        u = User.objects.get(username=args[0])
        print(u, u.user_locked, str(u.last_login))
        u.user_locked=True
        u.save()
        print(u, u.user_locked)
