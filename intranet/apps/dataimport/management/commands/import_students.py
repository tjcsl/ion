import csv
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from ....users.models import Email


class Command(BaseCommand):
    help = (
        "Given an alphabetized CSV of students from the same graduating class, add them to Ion. Required columns "
        "in the CSV include 'Student ID', 'First Name', 'Last Name', and 'Middle Name'. Optional fields include "
        "their 'Nick Name', 'Counselor' (last name), and 'Gender'."
    )

    def add_arguments(self, parser):
        parser.add_argument("--filename", dest="filename", type=str, required=True, help="Filename to import data from. Required.")
        parser.add_argument("--grad-year", dest="grad_year", type=str, required=True, help="Graduation year of this class. Required.")
        parser.add_argument(
            "--username-file", dest="username_file", type=str, default=None, help="If provided, write a CSV of usernames to this file."
        )
        parser.add_argument("--run", action="store_true", dest="run", default=False, help="Actually run.")
        parser.add_argument("--confirm", action="store_true", dest="confirm", default=False, help="Skip confirmation.")

    def ask(self, q):
        if input(f"{q} [Yy]: ").lower() != "y":
            self.stdout.write(self.style.ERROR("Abort."))
            sys.exit()

    def generate_single_username(
        self, users_properties: {}, graduating_year: int, first_name_header: str = "First Name", last_name_header: str = "Last Name"
    ) -> str:
        """Generate a single username. Ignores the presence of other users (so duplicate usernames are not handled).

        Args:
            users_properties: A dictionary with users' properties, typically a SIS export.
            graduating_year: The graduating year of the student.
            first_name_header: The key of the 'first name' field in the properties.
            last_name_header: The key of the 'last name' field in the properties.

        Returns:
            A single username.

        """
        # A few sanity checks
        if len(str(graduating_year)) != 4:
            raise ValueError(f"Invalid graduation year. Expected 4 digit year, got {len(str(graduating_year))}.")

        # Strip non alpha characters from first and last name.
        first_stripped = "".join([c for c in users_properties[first_name_header] if c.isalpha()])
        last_stripped = "".join([c for c in users_properties[last_name_header] if c.isalpha()])

        return f"{graduating_year}{first_stripped[0]}{last_stripped[:7]}".lower()

    def find_next_available_username(self, used_username: str, username_set: set = None) -> str:
        """Find the next available username.

        Args:
            used_username: The used username.
            username_set: An additional set of usernames to deduplicate against.
                Regardless of this argument, this method will check against the database.

        Returns:
            A username that has not been used. Increments the digit on the end, or tacks one on if it doesn't exist.
        """

        def increment_username(username: str):
            if not username[-1].isnumeric():
                username = username + "1"
            else:
                username = username[:-1] + str(int(username[-1]) + 1)
            return username

        new_username = used_username
        while get_user_model().objects.filter(username=new_username).exists() or (False if username_set is None else new_username in username_set):
            new_username = increment_username(new_username)

        return new_username

    def handle(self, *args, **options):
        # Read the data file
        with open(options["filename"], "r") as csvfile:
            data = list(csv.DictReader(csvfile))

        do_run = options["run"]
        if do_run:
            if not options["confirm"]:
                self.ask("Is the list alphabetized?")
                self.ask("Add new users?")
        else:
            self.stdout.write(self.style.WARNING("In pretend mode."))

        # Generate usernames
        # First, we generate usernames for each user, not looking at others
        # Store all the usernames in a set so we can refer to them later
        username_set = set()
        sid_set = set()
        for user in data:
            user["TJHSST_username"] = self.generate_single_username(user, options["grad_year"])
            username_set.add(user["TJHSST_username"])
            sid_set.add(user["Student ID"])

        # Now we query the database to see which usernames have already been taken
        qs = get_user_model().objects.filter(Q(username__in=username_set) | Q(student_id__in=sid_set))
        existing_usernames = set(qs.values_list("username", flat=True))

        # And for student IDs
        existing_student_ids = set(qs.values_list("student_id", flat=True))

        # Used to store actual usernames (after they have been deduplicated) to output to that file
        actual_username_list = []

        # Loop through our new users
        for new_user in data:
            # Prevent duplication of users
            if new_user["Student ID"] not in existing_student_ids:
                # Check to see if username already taken
                if new_user["TJHSST_username"] in existing_usernames:
                    new_user["TJHSST_username"] = self.find_next_available_username(new_user["TJHSST_username"], existing_usernames)

                # Append username to list
                actual_username_list.append(new_user["TJHSST_username"])

                # Now we can safely add this user
                if do_run:
                    counselor = get_user_model().objects.get(username=new_user["Counselor"].strip()) if "Counselor" in new_user.keys() else None
                    nickname = new_user["Nick Name"].strip() if "Nick Name" in new_user.keys() else ""
                    gender = (
                        new_user["Gender"].strip() == "M" if "Gender" in new_user.keys() else None
                    )  # TODO: is it "M" or "Male" or something else?
                    new_user_obj = get_user_model().objects.create(
                        username=new_user["TJHSST_username"],
                        student_id=new_user["Student ID"].strip(),
                        last_name=new_user["Last Name"].strip(),
                        first_name=new_user["First Name"].strip(),
                        middle_name=new_user["Middle Name"].strip(),
                        counselor=counselor,
                        nickname=nickname,
                        graduation_year=int(options["grad_year"]),
                        gender=gender,
                        receive_news_emails=True,
                        receive_eighth_emails=True,
                    )
                    # We must add their TJ email
                    Email.objects.create(address=f"{new_user['TJHSST_username']}@tjhsst.edu", user=new_user_obj)

                self.stdout.write(self.style.SUCCESS(f"Created user {new_user['TJHSST_username']}."))

                existing_usernames.add(new_user["TJHSST_username"])

            else:
                self.stdout.write(self.style.ERROR(f"User with SID {new_user['Student ID']} already exists."))

        if options["username_file"] is not None:
            with open(options["username_file"], "w") as file:
                csv_writer = csv.DictWriter(file, fieldnames=["Username"])
                csv_writer.writeheader()
                for username in actual_username_list:
                    csv_writer.writerow({"Username": username})
