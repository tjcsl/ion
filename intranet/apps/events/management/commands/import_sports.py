from django.core.management.base import BaseCommand

from ...tasks import pull_sports_schedules


class Command(BaseCommand):
    help = "Import sports schedule for specified month"

    def handle(self, *args, **options):
        pull_sports_schedules(options["month"])

    def add_arguments(self, parser):
        parser.add_argument("month", type=int)
