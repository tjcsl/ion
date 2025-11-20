from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthActivity
from intranet.apps.eighth.views.activities import generate_statistics_pdf


class Command(BaseCommand):
    help = "Generate a PDF file with statistics of all of the Eighth Activities."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-years",
            action="store_true",
            dest="years",
            default=False,
            help="Include statistics for all of the years. Overrides the --year flag, if set.",
        )
        parser.add_argument("--year", dest="year", default=None, type=int, help="The year to generate statistics for.")
        parser.add_argument("--output-file", default="eighth.pdf", dest="output", help="The location where the PDF file will be saved.")

    def handle(self, *args, **options):
        b = generate_statistics_pdf(EighthActivity.objects.all().order_by("name"), all_years=options["years"], year=options["year"])
        with open(options["output"], "wb") as f:
            f.write(b.read())
