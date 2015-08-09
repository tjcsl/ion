# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from intranet import settings
from intranet.apps.eighth.models import EighthBlock, EighthSignup
from intranet.apps.eighth.notifications import signup_status_email
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Notify users who have not signed up for Eighth Period."

    def handle(self, **options):
        users = User.objects.filter(receive_eighth_emails=True)
        next_blocks = EighthBlock.objects.get_next_upcoming_blocks()

        for user in users:
            user_signups = EighthSignup.objects.filter(user=user, scheduled_activity__block__in=next_blocks)
            if user_signups.count() < next_blocks.count():
                """User hasn't signed up for a block."""
                self.stdout.write("User {} hasn't signed up for a block".format(user))
                signup_status_email(user, next_blocks)
            elif user_signups.filter(scheduled_activity__cancelled=True).count() > 0:
                """User is in a cancelled activity."""
                self.stdout.write("User {} is in a cancelled activity.".format(user))
                signup_status_email(user, next_blocks)



        self.stdout.write("Done.")