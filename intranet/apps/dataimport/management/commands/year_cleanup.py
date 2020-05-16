import datetime
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from intranet.apps.eighth.models import EighthSignup
from intranet.utils.date import get_senior_graduation_year


class Command(BaseCommand):
    help = "Perform end-of-year cleanup duties."

    def add_arguments(self, parser):
        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Actually run.")
        parser.add_argument("--confirm", action="store_true", dest="confirm", default=False, help="Skip confirmation.")
        parser.add_argument(
            "--senior-graduation-year", dest="senior_grad_year", type=int, default=get_senior_graduation_year(), help="The senior graduation year",
        )

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            self.stdout.write("Abort.")
            sys.exit()

    def chk(self, q, test):
        if test:
            self.stdout.write("OK: %s" % q)
            return True
        else:
            self.stdout.write("ERROR: %s" % q)
            self.stdout.write("Abort.")
            return False

    def handle(self, *args, **options):
        do_run = options["run"]

        if do_run:
            if not options["confirm"]:
                self.ask(
                    "===== WARNING! =====\n\n"
                    "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                    "===== WARNING! =====\n\n"
                    "Continue?"
                )
        else:
            self.stdout.write("In pretend mode.")

        current_year = timezone.now().year
        new_senior_year = current_year + 1
        turnover_date = datetime.datetime(current_year, 7, 1)
        self.stdout.write("Turnover date set to: {}".format(turnover_date.strftime("%c")))

        senior_grad_year = options["senior_grad_year"]

        if not self.chk("senior_grad_year = {}".format(new_senior_year), senior_grad_year == new_senior_year):
            return
        """
        EIGHTH:
            EighthBlock: filtered
            EighthSignup: absences removed
            EighthActivity: keep

        ANNOUNCEMENTS:
            AnnouncementRequest: filtered

        USERS:
            User: graduated students deleted
        """

        self.stdout.write("Resolving absences")
        if do_run:
            self.clear_absences()

        self.stdout.write("Updating welcome state")
        if do_run:
            self.update_welcome()

        self.stdout.write("Deleting graduated users")
        if do_run:
            self.handle_delete(senior_grad_year=senior_grad_year)

        self.stdout.write("Archiving admin comments")
        if do_run:
            self.archive_admin_comments(senior_grad_year=senior_grad_year)

    def clear_absences(self):
        absents = EighthSignup.objects.filter(was_absent=True)
        self.stdout.write("{} absent eighth signups".format(absents.count()))
        for a in absents:
            a.archive_remove_absence()
        self.stdout.write("Archived absences")

    def update_welcome(self):
        get_user_model().objects.all().update(seen_welcome=False)

    def archive_admin_comments(self, *, senior_grad_year: int):
        for usr in get_user_model().objects.filter(user_type="student", graduation_year__gte=senior_grad_year):
            usr.archive_admin_comments()

    def handle_delete(self, *, senior_grad_year: int):
        for usr in get_user_model().objects.filter(graduation_year__lt=senior_grad_year).exclude(user_type="alum"):
            if not usr.is_superuser and not usr.is_staff:
                usr.handle_delete()
                self.stdout.write(str(usr.delete()))
            else:
                usr.user_type = "alum"
                usr.save()
                self.stdout.write("User {} KEEP".format(usr.username))
