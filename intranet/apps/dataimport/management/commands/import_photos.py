#!/usr/bin/env python3

import io
import sys
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from PIL import Image

from intranet.apps.users.models import Photo


class Command(BaseCommand):
    help = "Imports photos from yearbook data export"

    def add_arguments(self, parser):
        parser.add_argument("directory")
        parser.add_argument("--staff", action="store_true", dest="staff", default=False, help='Import staff photos in the format "Last-First.jpg"')

    def handle(self, *args, **options):
        PHOTO_ROOT_DIRECTORY = options["directory"]
        IS_STAFF = options["staff"]
        PHOTO_ROOT_PATH = Path(PHOTO_ROOT_DIRECTORY)
        sys.stdout.write(f"Preparing to import photos from directory {PHOTO_ROOT_DIRECTORY}\n")
        messages = []
        all_photos = list(PHOTO_ROOT_PATH.glob("*.jpg"))
        for path in all_photos:
            user = None
            if IS_STAFF:
                if "-" in path.stem:
                    last_name, first_name = path.stem.rsplit("-", 1)
                    user = get_user_model().objects.filter(first_name=first_name, last_name=last_name).first()
            else:
                try:
                    int(path.stem)
                    user = get_user_model().objects.user_with_student_id(path.stem)
                except ValueError:
                    pass

            if user is None:
                print(f"IGNORING {path.name}")
                continue

            grade_number = user.grade.number
            img = Image.open(path)
            img_arr = io.BytesIO()
            img.save(img_arr, format="JPEG")
            value = img_arr.getvalue()
            message = f"Creating photo for {user} grade {grade_number}"
            print(message)
            messages.append(message)
            Photo.objects.create(user=user, grade_number=grade_number, _binary=value)
        with open("photos_created.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(messages))

        sys.stdout.write("Completed photo import.\n")
