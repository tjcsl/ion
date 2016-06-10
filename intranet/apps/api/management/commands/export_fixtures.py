# -*- coding: utf-8 -*-
import os
import shutil
import datetime
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = "This command dumps the ion database to a series of fixture files."

    def add_arguments(self, parser):
        parser.add_argument("-f", "--folder", default=None, help="The folder to export fixtures to.")

    def handle(self, *args, **options):
        verbosity = options.get("verbosity", 1)
        fixtures_folder = options.get("folder")
        if not fixtures_folder:
            fixtures_folder = os.path.join(os.getcwd(), "fixtures")
            os.makedirs(fixtures_folder, exist_ok=True)
        if not os.path.isdir(fixtures_folder):
            raise CommandError("Script could not find fixtures folder!")
        print("Exporting to " + fixtures_folder)

        # Filter out all models that are not relevant to ion.
        models = [x.__module__ + "." + x.__name__ for x in apps.get_models()]
        modellist = []
        for model in models:
            if not model.startswith(tuple(settings.INSTALLED_APPS)):
                if verbosity > 1:
                    print("Skipping " + model + " (not in installed apps)")
                continue
            if not model.startswith(("intranet.apps.", "django.contrib.")) or ".models." not in model:
                if verbosity > 1:
                    print("Skipping " + model)
                continue
            modellist.append(model)

        # Find out what order the fixtures need to be loaded in.
        order = depend(set([relative_model_path(x).split(".")[0] for x in modellist]))
        order = [x.__module__ + "." + x.__name__ for x in order]

        # Save models to json files.
        modelcount = 0
        for absolutemodelpath in modellist:
            modelpath = relative_model_path(absolutemodelpath)
            buf = StringIO()
            try:
                call_command("dumpdata", modelpath, natural=True, stdout=buf)
            except CommandError as e:
                print("Failed " + modelpath)
                if verbosity > 1:
                    print(e)
                continue
            if buf.tell() <= 2:
                if verbosity > 1:
                    print("Skipping " + model + " (empty)")
                continue
            buf.seek(0)
            number = order.index(modelpath)
            modelfile = fixtures_folder + "/" + modelpath.split(".")[0] + "/" + str(number).zfill(4) + modelpath.split(".")[1] + ".json"
            modelfilepath = os.path.dirname(modelfile)
            if not os.path.isdir(modelfilepath):
                os.makedirs(modelfilepath)
            with open(modelfile, "w") as f:
                shutil.copyfileobj(buf, f)
            print("Exported " + absolutemodelpath)
            modelcount += 1

        # Write a readme with instructions on how to load the files.
        readme = open(fixtures_folder + "/README.txt", "w")
        readme.write("These ion fixtures were exported on %s with commit %s.\n" % (datetime.datetime.now().strftime("%H:%M %m/%d/%Y"), settings.GIT["commit_long_hash"]))
        readme.write("To load these fixtures, run \"./manage.py import_fixtures\"\n")
        readme.write("This command may take a long time if you have a lot of fixtures. There are %s fixtures in this directory." % modelcount)
        readme.close()


def relative_model_path(model):
    if model.startswith("intranet"):
        rel = model[len("intranet.apps."):]
    elif model.startswith("django"):
        rel = model[len("django.contrib."):]
    else:
        raise CommandError("Could not identify relative model path! " + model)
    return rel.replace(".models.", ".")


def depend(applist):
    model_deps = []
    for app in applist:
        models = apps.get_app_config(app).get_models()
        for model in models:
            deps = []

            # Check for absolute dependencies.
            if hasattr(model, "natural_key"):
                nat_deps = getattr(model.natural_key, "dependencies", [])
                if nat_deps:
                    print("Warning: Model " + str(model) + " has defined dependencies!")

            # Check dependencies for any fields.
            for field in model._meta.fields:
                if hasattr(field.rel, "to"):
                    rel_model = field.rel.to
                    deps.append(rel_model)

            # Check dependencies for many to many relationships.
            for field in model._meta.many_to_many:
                rel_model = field.rel.to
                if hasattr(rel_model, "natural_key"):
                    deps.append(rel_model)
            model_deps.append((model, deps))

    model_deps.reverse()
    model_list = []
    while model_deps:
        skipped = []
        changed = False
        while model_deps:
            model, deps = model_deps.pop()
            found = True
            for candidate in ((d not in models or d in model_list) for d in deps):
                if not candidate:
                    found = False
            if found:
                model_list.append(model)
                changed = True
            else:
                skipped.append(model)
        if not changed:
            raise CommandError("Failed to resolve dependencies!")
        model_deps = skipped
    return model_list
