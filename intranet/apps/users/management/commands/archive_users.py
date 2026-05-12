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
            help="Filename to import data from.",
        )
        parser.add_argument(
            "--column-header",
            dest="header",
            default="username",
            type=str,
            help="Header associated with the identifier column in the CSV.",
        )
        parser.add_argument(
            "--lookup-field",
            dest="lookup_field",
            default="username",
            type=str,
            help="User model field used to match identifiers (ex: username, student_id, email).",
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
            with open(filename, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    value = row.get(column_header)
                    if value:
                        identifiers.append(value.strip())
        except FileNotFoundError as e:
            raise CommandError(f"File not found: {filename}") from e
        except OSError as e:
            raise CommandError(f"Error reading file: {e}") from e
        return identifiers

    def handle(self, *args, **options):
        identifiers = self.read_identifiers(options["filename"], options["header"])
        if not identifiers:
            self.stdout.write(self.style.WARNING("No identifiers found in the CSV."))
            return

        total_identifiers = len(identifiers)
        unique_identifiers = list(dict.fromkeys(identifiers))
        duplicate_count = total_identifiers - len(unique_identifiers)

        user_model = get_user_model()
        lookup_field = options["lookup_field"]
        valid_fields = {field.name for field in user_model._meta.get_fields()}
        if lookup_field not in valid_fields:
            raise CommandError(f"Invalid lookup field: {lookup_field}")
        lookup_key = f"{lookup_field}__in"

        users = user_model.objects.filter(**{lookup_key: unique_identifiers})
        found_values = set(users.values_list(lookup_field, flat=True))
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
                "This script will archive users (lock accounts). Ensure that you\n"
                "have a properly backed-up copy of the database before proceeding.\n\n"
                "Continue?"
            ):
                self.stdout.write("Aborted.")
                return

        archived_count, already_archived_count = user_model.archive_users(users)
        self.stdout.write(self.style.SUCCESS(f"Archived users: {archived_count}"))
        if already_archived_count:
            self.stdout.write(self.style.WARNING(f"Already archived users: {already_archived_count}"))
