#!/usr/bin/env python3

import csv
import sys
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from intranet.utils.date import get_senior_graduation_year

from ....users.models import User


class Command(BaseCommand):
    help = "Update subschool administrator information, inheriting from each student's counselor"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "filename",
            type=str,
            nargs="?",
            default=None,
            help="Path to SIS import CSV with a Student ID column, and optionally an Administrator column",
        )

        parser.add_argument("--all", action="store_true", dest="all", default=False, help="Update every student who has not graduated")
        parser.add_argument(
            "--graduation-years",
            dest="graduation_years",
            nargs="+",
            type=int,
            default=None,
            metavar="YEAR",
            help="Update only students graduating in these years (e.g. --graduation-years 2027 2028)",
        )

        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Actually modifies the DB")

    def handle(self, *args: str, **kwargs: Any) -> None:
        filename = kwargs["filename"]
        all_students = kwargs["all"]
        graduation_years = kwargs["graduation_years"]

        if sum(map(bool, (filename, all_students, graduation_years))) != 1:
            raise CommandError("Pass exactly one of: a CSV filename, --all, or --graduation-years")

        to_run = kwargs["run"]

        if not to_run:
            sys.stdout.write(
                """This script is running in pretend mode.
Pass --run to actually run this script.
Please MAKE SURE you have updated info before running this script.
Actually running is a destructive operation.
"""
            )

        # Collect the students to work through, paired with any administrator named for them
        targets = []
        if filename:
            try:
                with open(filename, encoding="utf-8") as f:
                    data = list(csv.DictReader(f))
            except OSError as ex:
                raise CommandError(str(ex)) from ex

            if data and "Student ID" not in data[0]:
                raise CommandError(f"{filename} has no 'Student ID' column")

            for row in data:
                sid = row["Student ID"].strip()
                user = get_user_model().objects.user_with_student_id(sid)
                if user is None:
                    sys.stdout.write(f"There is no Ion account found for SID {sid}\n")
                    continue

                targets.append((user, (row.get("Administrator") or "").strip()))
        else:
            # Every one of these runs through the counselor chain, so pull it in up front
            students = get_user_model().objects.filter(user_type="student").select_related("counselor__administrator")
            if graduation_years:
                students = students.filter(graduation_year__in=graduation_years)
            else:
                students = students.filter(graduation_year__gte=get_senior_graduation_year())

            sys.stdout.write(f"Working through {students.count()} student(s).\n")
            targets = [(user, "") for user in students]

        # One transaction, so a failure part way through does not split students across administrators
        with transaction.atomic():
            for user, listed_name in targets:
                administrator = self.resolve_administrator(user, listed_name)
                if administrator is None:
                    continue

                if administrator != user.administrator:
                    sys.stdout.write(f"Switching administrator for {user.username} from {user.administrator} to {administrator}\n")
                    if to_run:
                        user.administrator = administrator
                        user.save(update_fields=["administrator"])

    def resolve_administrator(self, user: User, listed_name: str) -> User | None:
        """Returns the administrator to assign ``user``, or ``None`` if it cannot be determined."""
        # Kept out of handle() because the try/except around the lookup, plus the counselor
        # fallback, pushes handle() past the complexity limit when inlined.
        # We assume every administrator has a unique last name
        name = listed_name.split(",")[0].strip()
        if name:
            try:
                return get_user_model().objects.get(user_type="teacher", last_name=name)
            except get_user_model().DoesNotExist:
                sys.stdout.write(f"There is no teacher account found with last name {name}\n")
                return None
            except get_user_model().MultipleObjectsReturned:
                sys.stdout.write(f"There are multiple teacher accounts with last name {name}\n")
                return None

        # Nothing named explicitly, so inherit from the counselor
        if user.counselor is None:
            sys.stdout.write(f"{user.username} has no administrator listed and no counselor to inherit one from\n")
            return None

        if user.counselor.administrator is None:
            sys.stdout.write(f"Counselor {user.counselor} has no administrator set, so {user.username} cannot inherit one\n")
            return None

        return user.counselor.administrator
