import csv

from django.core.management.base import BaseCommand

from ...models import College


class Command(BaseCommand):
    help = "Import colleges from ceeb.csv file"

    def handle(self, *args, **options):
        with open("ceeb.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                ceeb, name, city, state = row
                College.objects.create(ceeb=ceeb, name=("{} - {}, {}".format(name, city, state)).title())
        # custom additions
        College.objects.create(ceeb=-1, name="University of Swamp (Harvard of the South) - The South")
