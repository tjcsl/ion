from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthSignup
from intranet.apps.eighth.notifications import absence_notification


class Command(BaseCommand):
    help = "Push notify users who have an Eighth Period absence (via Webpush.)"

    def add_arguments(self, parser):
        parser.add_argument("--silent", action="store_true", dest="silent", default=False, help="Be silent.")

        parser.add_argument("--pretend", action="store_true", dest="pretend", default=False, help="Pretend, and don't actually do anything.")

    def handle(self, *args, **options):
        log = not options["silent"]

        absences = EighthSignup.objects.get_absences().filter(absence_notified=False)

        for signup in absences:
            if log:
                self.stdout.write(str(signup))
            if not options["pretend"]:
                absence_notification(signup)
                signup.absence_notified = True
                signup.save()

        if log:
            self.stdout.write("Done.")
