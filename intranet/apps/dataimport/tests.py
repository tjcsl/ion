from datetime import datetime
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from ...test.ion_test import IonTestCase


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
