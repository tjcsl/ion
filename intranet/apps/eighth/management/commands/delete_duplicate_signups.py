import sys

from django.core.management.base import BaseCommand
from django.db.models import Count

from intranet.apps.eighth.models import EighthSignup


class Command(BaseCommand):
    help = "Delete duplicate Eighth signups and keep the most recent."

    def handle(self, *args, **options):
        duplicates = EighthSignup.objects.values("user", "scheduled_activity__block")
        duplicates = duplicates.annotate(Count("user"), Count("scheduled_activity__block")).order_by().filter(scheduled_activity__block__count__gt=1)
        num_duplicates = duplicates.count()
        for x in duplicates:
            signups = EighthSignup.objects.filter(user__id=x["user"], scheduled_activity__block__id=x["scheduled_activity__block"])
            signups = EighthSignup.objects.filter(pk__in=signups.order_by("-time").values_list("pk")[1:])
            signups.delete()
        sys.stdout.write("Deleted {} duplicate signup(s).\n".format(num_duplicates))
