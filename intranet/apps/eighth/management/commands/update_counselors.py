#!/usr/bin/env python3

import csv
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Update counselor information"

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="Path to SIS import CSV with a Student ID and Counselor column")

        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Actually modifies the DB")

    def handle(self, *args, **kwargs):
        data = []
        # We assume that the provided file has up-to-date information.
        # DO NOT RUN IF YOU DON'T HAVE UP-TO-DATE INFORMATION
        filename = kwargs["filename"]

        to_run = kwargs["run"]

        if not to_run:
            sys.stdout.write("This script is running in pretend mode.\n")
            sys.stdout.write("Pass --run to actually run this script.\n")
            sys.stdout.write("Please MAKE SURE you have updated info before running this script.\n")
            sys.stdout.write("Actually running is a destructive operation.\n")

        with open(filename) as f:
            contents = csv.DictReader(f)
            data = list(contents)

        counselors = get_user_model().objects.filter(user_type="counselor")

        for row in data:
            sid = row["Student ID"].strip()
            # We assume that every single counselor has a unique last name
            # If this is not true, please edit this file
            counselor = row["Counselor"].split(",")[0].strip()
            counselor = counselors.get(last_name=counselor)
            u = get_user_model().objects.user_with_student_id(sid)
            if u is None:
                sys.stdout.write("There is no Ion account found for SID {}\n".format(sid))
                continue

            if counselor != u.counselor:
                sys.stdout.write("Switching counselor for SID {} from {} to {}\n".format(sid, u.counselor, counselor))
                if to_run:
                    u.counselor = counselor
                    u.save()
