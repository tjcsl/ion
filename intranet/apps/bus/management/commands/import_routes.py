import csv

from django.core.management.base import BaseCommand

from ...models import Route


class Command(BaseCommand):
    help = "Import Routes from routes.csv"

    def handle(self, *args, **options):
        with open("routes.csv", encoding="utf-8") as f:
            reader = csv.reader(f)
            print("Deleting preexisting buses")
            for row in reader:
                (name,) = row
                _, created = Route.objects.get_or_create(route_name=name)
                if created:
                    print(f"Created route {name}")
                else:
                    print("Route {} already exists")
