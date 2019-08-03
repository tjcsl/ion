from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from intranet.apps.eighth.models import EighthBlock, EighthSignup
from intranet.apps.eighth.notifications import signup_status_email


class Command(BaseCommand):
    help = "Notify users who have not signed up for Eighth Period or need to change their signup selection."

    def add_arguments(self, parser):
        parser.add_argument("--silent", action="store_true", dest="silent", default=False, help="Be silent.")

        parser.add_argument(
            "--only-tomorrow", action="store_true", dest="only-tomorrow", default=False, help="Only run if there is a block tomorrow."
        )

        parser.add_argument("--only-today", action="store_true", dest="only-today", default=False, help="Only run if there is a block today.")

        parser.add_argument("--pretend", action="store_true", dest="pretend", default=False, help="Pretend, and don't actually do anything.")

        parser.add_argument(
            "--everyone", action="store_true", dest="everyone", default=False, help="Send to everyone, even those who have no eighth emails set."
        )

    def handle(self, *args, **options):

        log = not options["silent"]
        if options["everyone"]:
            users = get_user_model().objects.get_students()
        else:
            users = get_user_model().objects.filter(receive_eighth_emails=True)
        next_blocks = EighthBlock.objects.get_next_upcoming_blocks()

        if next_blocks.count() < 1:
            if log:
                self.stdout.write("No upcoming blocks.")
            return

        today = timezone.localdate()
        if options["only-tomorrow"]:
            tomorrow = today + timedelta(days=1)
            blk_date = next_blocks[0].date
            if blk_date != tomorrow:
                if log:
                    self.stdout.write("Block {} on {} is not tomorrow ({}).".format(next_blocks[0], blk_date, tomorrow))
                return

        if options["only-today"]:
            blk_date = next_blocks[0].date
            if blk_date != today:
                if log:
                    self.stdout.write("Block {} on {} is not today ({}).".format(next_blocks[0], blk_date, today))
                return

        if log:
            self.stdout.write("{}".format(next_blocks))
            self.stdout.write("{}".format(options))
            self.stdout.write("{}".format(users))

        for user in users:
            user_signups = EighthSignup.objects.filter(user=user, scheduled_activity__block__in=next_blocks)
            if user_signups.count() < next_blocks.count():
                """User hasn't signed up for a block."""
                if log:
                    self.stdout.write("User {} hasn't signed up for a block".format(user))
                if not options["pretend"]:
                    try:
                        signup_status_email(user, next_blocks)
                    except Exception as e:
                        self.stdout.write(e)
            elif user_signups.filter(scheduled_activity__cancelled=True).count() > 0:
                """User is in a cancelled activity."""
                if log:
                    self.stdout.write("User {} is in a cancelled activity.".format(user))
                if not options["pretend"]:
                    try:
                        signup_status_email(user, next_blocks)
                    except Exception as e:
                        self.stdout.write(e)

        if log:
            self.stdout.write("Done.")
