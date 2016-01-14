import csv

from django.core.management.base import BaseCommand

from ...models import College


class Command(BaseCommand):
    help = "Import colleges from ceeb.csv file"

    def handle(self, *args, **options):
        reader = csv.reader(open("ceeb.csv", "r"))
        for row in reader:
            ceeb, name, city, state = row
            College.objects.create(ceeb=ceeb, name=("{} - {}, {}".format(name, city, state)).title())
