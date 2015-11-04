# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from intranet import settings
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Input users into the database who have not logged in already"

    def handle(self, **options):
        # FIXME: document the meaning of the magic numbers.
        users = [User.objects.user_with_ion_id(i) for i in range(14203, 14681)] + [User.objects.user_with_ion_id(i) for i in range(31416, 35000)]
        self.stdout.write("Looped through {} IDs.".format(len(users)))
