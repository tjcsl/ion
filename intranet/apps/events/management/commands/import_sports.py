from django.core.management.base import BaseCommand

from ...tasks import pull_sports_schedules


class Command(BaseCommand):
    help = "Import sports schedule for specified month (or current + next if omitted)"

    def add_arguments(self, parser):
        parser.add_argument("month", nargs="?", type=int, help="Optional month (1-12)")

    def handle(self, *args, **options):
        month = options.get("month")
        pull_sports_schedules(month)
