#!/usr/bin/env python3

import io
import sys
from pathlib import Path

from PIL import Image

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from intranet.apps.users.models import Photo


class Command(BaseCommand):
    help = "Imports photos from yearbook data export"

    def add_arguments(self, parser):
        parser.add_argument("directory")

    def handle(self, *args, **options):
        PHOTO_ROOT_DIRECTORY = options["directory"]
        PHOTO_ROOT_PATH = Path(PHOTO_ROOT_DIRECTORY)
        sys.stdout.write("Preparing to import photos from directory {}\n".format(PHOTO_ROOT_DIRECTORY))
        messages = []
        all_photos = list(PHOTO_ROOT_PATH.glob("*.jpg"))
        for path in all_photos:
            try:
                int(path.stem)
            except ValueError:
                print("IGNORING {}".format(path.name))
                continue
            user = get_user_model().objects.user_with_student_id(path.stem)
            if user is None:
                print("IGNORING {}".format(path.name))
                continue

            grade_number = user.grade.number
            img = Image.open(path)
            img_arr = io.BytesIO()
            img.save(img_arr, format="JPEG")
            value = img_arr.getvalue()
            message = "Creating photo for {} grade {}".format(user, grade_number)
            print(message)
            messages.append(message)
            Photo.objects.create(user=user, grade_number=grade_number, _binary=value)
        with open("photos_created.txt", "w") as f:
            f.write("\n".join(messages))

        sys.stdout.write("Completed photo import.\n")
