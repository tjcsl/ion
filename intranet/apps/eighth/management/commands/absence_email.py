from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthSignup
from intranet.apps.eighth.notifications import absence_email


class Command(BaseCommand):
    help = "Notify users who have an Eighth Period absence."

    def add_arguments(self, parser):
        parser.add_argument("--silent", action="store_true", dest="silent", default=False, help="Be silent.")

        parser.add_argument("--pretend", action="store_true", dest="pretend", default=False, help="Pretend, and don't actually do anything.")

    def handle(self, *args, **options):

        log = not options["silent"]

        absences = EighthSignup.objects.get_absences().filter(absence_emailed=False)

        for signup in absences:
            if log:
                self.stdout.write("{}".format(signup))
            if not options["pretend"]:
                absence_email(signup)
                signup.absence_emailed = True
                signup.save()

        if log:
            self.stdout.write("Done.")
