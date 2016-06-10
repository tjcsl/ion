# -*- coding: utf-8 -*-
import os
import fnmatch

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "This command populates the ion database from a series of fixture files."

    def add_arguments(self, parser):
        parser.add_argument("-f", "--folder", default=None, help="The folder to import fixtures from.")
        parser.add_argument("-t", action="store_true", dest="test", default=False, help="List the fixture order without importing the fixtures.")

    def handle(self, *args, **options):
        verbosity = options.get("verbosity", 1)
        fixtures_folder = options.get("folder")
        if not fixtures_folder:
            fixtures_folder = os.path.join(os.getcwd(), "fixtures")
            os.makedirs(fixtures_folder, exist_ok=True)
        if not os.path.isdir(fixtures_folder):
            raise CommandError("Script could not find fixtures folder!")
        print("Importing from " + fixtures_folder)

        # Find all json files in folder.
        fixtures = []
        for root, dirnames, filenames in os.walk(fixtures_folder):
            for filename in fnmatch.filter(filenames, "*.json"):
                fixtures.append(os.path.join(root, filename))

        # Sort by first four characters of file name.
        fixtures = sorted(fixtures, key=lambda item: int(item.split("/")[-1][:4]))

        if options["test"]:
            for x in fixtures:
                print(x[len(fixtures_folder):])
            return

        # Import fixtures
        for x in fixtures:
            try:
                call_command("loaddata", x)
                if verbosity > 1:
                    print("Loaded " + x)
            except Exception as e:
                print("Failed to import %s (%s)" % (x, type(e).__name__))
                if verbosity > 1:
                    print(e)
