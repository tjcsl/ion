# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.eighth.models import EighthActivity
from intranet.apps.eighth.views.activities import generate_statistics_pdf


class Command(BaseCommand):
    help = "Generate a PDF file with statistics of all of the Eighth Activities."

    def add_arguments(self, parser):
        parser.add_argument('--all-years', action='store_true', dest='years', default=False, help="Include statistics for all of the years.")
        parser.add_argument('--output-file', default='eighth.pdf', dest='output', help="The location where the PDF file will be saved.")

    def handle(self, *args, **options):
        b = generate_statistics_pdf(EighthActivity.objects.all().order_by("name"), all_years=options["years"])
        with open(options["output"], "wb") as f:
            f.write(b.read())
