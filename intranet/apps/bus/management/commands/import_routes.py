# -*- coding: utf-8 -*-
import csv

from django.core.management.base import BaseCommand

from ...models import Route


class Command(BaseCommand):
    help = "Import Routes from routes.csv"

    def handle(self, *args, **options):
        reader = csv.reader(open("routes.csv", "r"))
        print("Deleting preexisting buses")
        Route.objects.all().delete()
        for row in reader:
            name, = row
            print("Adding bus {}".format(name))
            Route.objects.create(route_name=name, status="o")
