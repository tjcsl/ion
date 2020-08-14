from datetime import datetime
from io import StringIO
from unittest.mock import mock_open, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from ...test.ion_test import IonTestCase
from .management.commands.import_students import Command as import_students


class YearCleanupTest(IonTestCase):
    """Tests end of year cleanup."""

    def test_year_cleanup(self):
        out = StringIO()
        year = timezone.now().year
        turnover_date = datetime(year, 7, 1)
        call_command("year_cleanup", stdout=out, senior_grad_year=year + 1)
        output = [
            "In pretend mode.",
            "Turnover date set to: {}".format(turnover_date.strftime("%c")),
            "OK: senior_grad_year = {}".format(year + 1),
            "Resolving absences",
            "Updating welcome state",
            "Deleting graduated users",
            "Archiving admin comments",
        ]
        self.assertEqual(out.getvalue().splitlines(), output)


class DeleteUsersTest(IonTestCase):
    """Tests deletion of users."""

    def test_delete_users(self):
        # Add some users
        users = [
            {"student_id": "12345", "username": "2021ttest", "first_name": "Test"},
            {"student_id": "54321", "username": "2021ttest2", "first_name": "Testtwo"},
            {"student_id": "11111", "username": "2021ttester", "first_name": "Testfive"},
        ]
        for user in users:
            newuser = get_user_model().objects.get_or_create(**user)
            newuser[0].save()

        call_command("delete_users", student_ids=["12345", "54321", "55555"], run=True, confirm=True)

        # Check if first and second users were deleted
        with self.assertRaises(get_user_model().DoesNotExist):
            get_user_model().objects.get(username="2021ttest")

        with self.assertRaises(get_user_model().DoesNotExist):
            get_user_model().objects.get(username="2021ttest2")

        # Check if the third user was left intact
        self.assertEqual("2021ttester", get_user_model().objects.get(username="2021ttester").username)


class ImportStudentsTest(IonTestCase):
    """Tests importing students."""

    def test_generate_username(self):
        valid_test_cases = [
            ("2023jdoe", {"First Name": "John", "Last Name": "Doe", "grad_year": 2023}),
            ("2023alongest", {"First Name": "Alice", "Last Name": "Longestlastnameintheworld", "grad_year": 2023}),
            ("2023jdoe", {"First Name": "John", "Last Name": "Doe", "grad_year": 2023}),
            ("2023jdoesome", {"First Name": "John", "Last Name": "Doe-Something-To-Trip-This-Up", "grad_year": 2023}),
        ]
        for expected, data in valid_test_cases:
            self.assertEqual(expected, import_students.generate_single_username(None, data, data["grad_year"]))

        with self.assertRaises(ValueError):
            import_students.generate_single_username(None, valid_test_cases[0][1], 20394204)

        with self.assertRaises(KeyError):
            import_students.generate_single_username(None, valid_test_cases[0][1], 2021, first_name_header="Invalid First Name")

        with self.assertRaises(KeyError):
            import_students.generate_single_username(None, valid_test_cases[0][1], 2023, last_name_header="Invalid last Name")

    def test_find_next_username(self):
        # Make some users
        get_user_model().objects.create(username="2021ttest")
        get_user_model().objects.create(username="2021ttest1")
        get_user_model().objects.create(username="2021ttest3")

        self.assertEqual("2021ttest2", import_students.find_next_available_username(None, "2021ttest"))

        # Make some more users
        get_user_model().objects.create(username="2021ttest2")
        get_user_model().objects.create(username="2021ttest4")

        self.assertEqual("2021ttest5", import_students.find_next_available_username(None, "2021ttest"))

        # Now let's try using a set
        s = {"2021ttest5", "2021ttest6", "2021ttest7"}
        self.assertEqual("2021ttest8", import_students.find_next_available_username(None, "2021ttest", s))

        # Test file input
        file_contents = "Student ID\n11111\n55555"
        with patch("intranet.apps.dataimport.management.commands.delete_users.open", mock_open(read_data=file_contents)) as m:
            call_command("delete_users", filename="foo.csv", header="Student ID", run=True, confirm=True)

        m.assert_called_with("foo.csv", "r")
        with self.assertRaises(get_user_model().DoesNotExist):
            get_user_model().objects.get(username="2021ttester")
