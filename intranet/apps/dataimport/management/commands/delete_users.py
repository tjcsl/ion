import csv
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Given a list of FCPS student IDs, delete them if they exist."

    def add_arguments(self, parser):
        parser.add_argument("--filename", dest="filename", type=str, help="Filename to import data from. Must supply either this or 'student-id'.")
        parser.add_argument(
            "--column-header",
            dest="header",
            default="Student ID",
            type=str,
            help="Header associated with the student ID column. Use with the 'filename' option",
        )
        parser.add_argument(
            "--student-id", dest="student_ids", nargs="+", help="A space-separated list of student IDs to remove. Must supply this or 'filename'."
        )
        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Actually run.")
        parser.add_argument("--confirm", action="store_true", dest="confirm", default=False, help="Skip confirmation.")

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            self.stdout.write(self.style.ERROR("Abort."))
            sys.exit()

    def read_student_ids(self, filename: str, column_header: str):
        """Read student IDs from the given filename.

        Args:
            filename: Filename of the CSV to read from.
            column_header: Column header of the Student ID column.

        Returns:
            A list of user IDs.

        """
        ids = []
        with open(filename, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ids.append(row[column_header])
        return ids

    def handle(self, *args, **options):
        # Sanity check
        if options["student_ids"] is None and options["filename"] is None:
            raise ValueError("Must provide one of filename or student_id")

        # Read in the list of student IDs, either from args or from the given filename
        if options["student_ids"] is None:
            ids = self.read_student_ids(options["filename"], options["header"])
        else:
            ids = options["student_ids"]

        # Get a list of user model instances
        users = get_user_model().objects.filter(student_id__in=ids)

        self.stdout.write(self.style.WARNING("These users are about to be deleted."))
        self.stdout.write(str(users.values_list("username", flat=True)))

        do_run = options["run"]
        if do_run:
            if not options["confirm"]:
                self.ask(
                    "===== WARNING! =====\n\n"
                    "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                    "===== WARNING! =====\n\n"
                    "Continue?"
                )
        else:
            self.stdout.write("In pretend mode.")

        if do_run:
            for user in users:
                user.handle_delete()
                user.delete()

                self.stdout.write(self.style.SUCCESS(f"Deleted user {user.username}."))
