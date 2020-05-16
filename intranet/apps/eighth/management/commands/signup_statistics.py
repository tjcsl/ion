import csv
import datetime
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone

from intranet.apps.eighth.models import EighthActivity
from intranet.utils.date import get_date_range_this_year


class Command(BaseCommand):
    help = "Generate attendance statistics for an eighth period activity as a CSV."

    def add_arguments(self, parser):
        parser.add_argument("activity_id", help="The ID of the activity to generate statistics for.")

        parser.add_argument(
            "--start-date", help="The start date for statistics generation (default: start of the year)", dest="start_date", default=None
        )
        parser.add_argument("--end-date", help="The end date for statistics generation (default: end of the year)", dest="end_date", default=None)

        parser.add_argument("--outfile", dest="outfile", help="Output file name", default=None)

        parser.add_argument(
            "--min-blocks", dest="min_blocks", type=int, default=1, help="The minimum number of blocks a user must attend to be included."
        )

    def handle(self, *args, **options):
        start_date, end_date = get_date_range_this_year()

        if options.get("start_date") is not None:
            start_date = timezone.make_aware(datetime.datetime.strptime("%Y-%m-%d", options["start_date"])).date()

        if options.get("end_date") is not None:
            end_date = timezone.make_aware(datetime.datetime.strptime("%Y-%m-%d", options["end_date"])).date()

        try:
            activity = EighthActivity.objects.get(id=options["activity_id"])
        except EighthActivity.DoesNotExist:
            raise CommandError("Activity not found")

        rows = [
            ("TJ Username", "First Name", "Last Name", "Number of Signups"),
            *get_user_model()
            .objects.annotate(
                signup_count=Count(
                    "eighthsignup",
                    filter=Q(
                        eighthsignup__scheduled_activity__block__date__gte=start_date,
                        eighthsignup__scheduled_activity__block__date__lte=end_date,
                        eighthsignup__scheduled_activity__activity=activity,
                    ),
                ),
            )
            .filter(signup_count__gte=options["min_blocks"])
            .order_by("-signup_count", "last_name", "username")
            .values_list("username", "first_name", "last_name", "signup_count"),
        ]

        if options.get("outfile") is None:
            writer = csv.writer(sys.stdout)
            writer.writerows(rows)
        else:
            with open(options.get("outfile"), "w") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
