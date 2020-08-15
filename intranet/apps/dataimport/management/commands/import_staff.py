import csv
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ....users.models import Email


class Command(BaseCommand):
    help = (
        "Given an CSV of staff, add them to Ion. Required columns include 'Username', 'First Name', 'Last Name', "
        "and 'Middle Name'. Optional columns include 'Nick Name' and 'Gender'."
    )

    def add_arguments(self, parser):
        parser.add_argument("--filename", dest="filename", type=str, required=True, help="Filename to import data from. Required.")
        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Actually run.")
        parser.add_argument("--confirm", action="store_true", dest="confirm", default=False, help="Skip confirmation.")

    def ask(self, q):
        if input(f"{q} [Yy]: ").lower() != "y":
            self.stdout.write(self.style.ERROR("Abort."))
            sys.exit()

    def handle(self, *args, **options):
        # Read the data file
        with open(options["filename"], "r") as csvfile:
            data = list(csv.DictReader(csvfile))

        do_run = options["run"]
        if do_run:
            if not options["confirm"]:
                self.ask("Add new users?")
        else:
            self.stdout.write(self.style.WARNING("In pretend mode."))

        # Loop through our new users
        for new_user in data:
            nickname = new_user["Nick Name"].strip() if "Nick Name" in new_user.keys() else ""
            gender = new_user["Gender"].strip() == "M" if "Gender" in new_user.keys() else None  # TODO: is it "M" or "Male" or something else?
            if do_run:
                new_user_obj = get_user_model().objects.get_or_create(
                    username=new_user["Username"],
                    last_name=new_user["Last Name"].strip(),
                    first_name=new_user["First Name"].strip(),
                    middle_name=new_user["Middle Name"].strip(),
                    nickname=nickname,
                    gender=gender,
                    receive_news_emails=True,
                    receive_eighth_emails=True,
                    user_type="teacher",
                )
                # We must add their TJ email
                Email.objects.get_or_create(address=f"{new_user['Username']}@fcps.edu", user=new_user_obj[0])
            else:
                # Simulate adding a new teacher
                new_user_obj = (None, True)

            if new_user_obj[1]:
                self.stdout.write(self.style.SUCCESS(f"Created user {new_user['Username']}."))
            else:
                self.stdout.write(self.style.ERROR(f"User {new_user['Username']} already exists."))
