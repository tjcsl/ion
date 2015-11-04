# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Input users into the database who have not logged in already"

    def handle(self, **options):
        # The range for Ion user IDs; adjust as needed
        ION_ID_START = 31416
        ION_ID_END = 33503
        self.stdout.write("ID range: {} - {}".format(ION_ID_START, ION_ID_END))
        users = [User.objects.user_with_ion_id(i) for i in range(ION_ID_START, ION_ID_END + 1)]
        self.stdout.write("Looped through {} IDs.".format(len(users)))
