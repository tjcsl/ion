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
            fixtures_folder = os.getcwd() + "/fixtures"
        if not os.path.isdir(fixtures_folder):
            raise CommandError("Script could not find fixtures folder!")
        print("Exporting to " + fixtures_folder)

        # Filter out all models that are not relevant to ion.
        models = [x.__module__ + "." + x.__name__ for x in apps.get_models()]
        modellist = []
        for model in models:
            if model.startswith("django"):
                continue
            if not model.startswith(tuple(settings.INSTALLED_APPS)):
                if verbosity > 1:
                    print("Skipping " + model)
                continue
            if not model.startswith("intranet.apps.") or ".models." not in model:
                if verbosity > 1:
                    print("Skipping " + model)
                continue
            modelpath = model[len("intranet.apps."):].replace(".models.", ".")
            modellist.append(modelpath)

        # Find out what order the fixtures need to be loaded in.
        order = depend(set([x.split(".")[0] for x in modellist]))
        order = [x.__module__ + "." + x.__name__ for x in order]
        order = [x[len("intranet.apps."):].replace(".models.", ".") for x in order]

        # Save models to json files.
        for modelpath in modellist:
            buf = StringIO()
            try:
                call_command("dumpdata", modelpath, stdout=buf)
            except CommandError as e:
                print("Failed " + modelpath)
                print(e)
                continue
            buf.seek(0)
            number = order.index(modelpath)
            modelfile = fixtures_folder + "/" + modelpath.split(".")[0] + "/" + str(number).zfill(4) + modelpath.split(".")[1] + ".json"
            modelfilepath = os.path.dirname(modelfile)
            if not os.path.isdir(modelfilepath):
                os.makedirs(modelfilepath)
            with open(modelfile, "w") as f:
                shutil.copyfileobj(buf, f)
            print("Exported " + modelpath)

        # Write a readme with instructions on how to load the files.
        readme = open(fixtures_folder + "/README.txt", "w")
        readme.write("These fixtures were exported on %s with commit %s. To load these fixtures, run the command:\n" % (datetime.datetime.now().strftime("%H:%M %m/%d/%Y"), settings.GIT["commit_long_hash"]))
        readme.write("find ./fixtures/ -name '*.json' -printf '%f %p\\n' | sort | cut -d' ' -f2- | xargs ./manage.py loaddata\n")
        readme.write("This command may take a long time if you have a lot of fixtures.")
        readme.close()


def depend(applist):
    model_deps = []
    for app in applist:
        models = apps.get_app_config(app).get_models()
        for model in models:
            deps = []
            for field in model._meta.fields:
                if hasattr(field.rel, "to"):
                    rel_model = field.rel.to
                    deps.append(rel_model)
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
