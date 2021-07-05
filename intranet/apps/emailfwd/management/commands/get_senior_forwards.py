from django.core.management.base import BaseCommand

from .....utils.date import get_senior_graduation_year
from ....emailfwd.models import SeniorEmailForward


class Command(BaseCommand):
    help = "Gets all senior email forwards"

    def handle(self, *args, **options):
        forwards = SeniorEmailForward.objects.filter(user__graduation_year=get_senior_graduation_year(), user__user_type="student")
        for forward in forwards:
            self.stdout.write("%s:\t\t%s" % (forward.user, forward.email))
