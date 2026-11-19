import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Archive users (lock accounts) from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--filename",
            dest="filename",
            type=str,
            required=True,
            help="CSV file with 'username' column containing usernames to archive.",
        )
        parser.add_argument(
            "--run",
            action="store_true",
            dest="run",
            help="Actually run.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            dest="confirm",
            help="Skip confirmation prompt (only applies with --run).",
        )

    def ask(self, q) -> bool:
        return input(f"{q} [y/N]: ").strip().lower() == "y"

    def read_identifiers(self, filename: str, column_header: str):
        identifiers = []
        try:
            with open(filename, encoding="utf-8-sig", newline="") as csvfile:
                reader = csv.DictReader(csvfile, strict=True)
                if not reader.fieldnames or column_header not in reader.fieldnames:
                    raise CommandError(f"CSV must contain a '{column_header}' column.")
                for row in reader:
                    value = (row.get(column_header) or "").strip()
                    if value:
                        identifiers.append(value)
        except FileNotFoundError as e:
            raise CommandError(f"File not found: {filename}") from e
        except (OSError, UnicodeError, csv.Error) as e:
            raise CommandError(f"Error reading file: {e}") from e
        return identifiers

    def handle(self, *args, **options):
        identifiers = self.read_identifiers(options["filename"], "username")
        if not identifiers:
            self.stdout.write(self.style.WARNING("No identifiers found in the CSV."))
            return

        total_identifiers = len(identifiers)
        unique_identifiers = list(dict.fromkeys(identifiers))
        duplicate_count = total_identifiers - len(unique_identifiers)

        users = get_user_model().objects.filter(username__in=unique_identifiers)
        found_values = set(users.values_list("username", flat=True))
        missing = sorted(value for value in unique_identifiers if value not in found_values)

        self.stdout.write(f"Identifiers provided: {total_identifiers}")
        self.stdout.write(f"Unique identifiers: {len(unique_identifiers)}")
        if duplicate_count:
            self.stdout.write(self.style.WARNING(f"Duplicate identifiers: {duplicate_count}"))
        self.stdout.write(f"Matched users: {users.count()}")
        self.stdout.write(f"Missing identifiers: {len(missing)}")
        if missing:
            self.stdout.write(self.style.WARNING(str(missing)))

        if not options["run"]:
            self.stdout.write("Dry run mode.")
            return

        if not options["confirm"]:
            if not self.ask(
                "This script will archive users (lock accounts). Ensure\nthat you know what you're doing before proceeding.\n\nContinue?"
            ):
                self.stdout.write("Aborted.")
                return

        archived_count, already_archived_count = users.archive_users()
        self.stdout.write(self.style.SUCCESS(f"Archived users: {archived_count}"))
        if already_archived_count:
            self.stdout.write(self.style.WARNING(f"Already archived users: {already_archived_count}"))
