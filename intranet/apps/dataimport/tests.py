from datetime import datetime
from io import StringIO
from unittest.mock import mock_open, patch

import pytz

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
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

    def test_actual_year_cleanup(self):
        # Add some users
        user_2020 = get_user_model().objects.get_or_create(username="2020jdoe", graduation_year=2020, user_type="student")[0]
        sysadmin_user_2020 = get_user_model().objects.get_or_create(
            username="2020jdoe1", graduation_year=2020, user_type="student", is_superuser=True
        )[0]
        user_2021 = get_user_model().objects.get_or_create(
            username="2021jdoe", graduation_year=2021, user_type="student", admin_comments="haha this is test", seen_welcome=True
        )[0]

        # Give user_2021 an eighth absence
        eighth_block = EighthBlock.objects.create(date="2020-03-13", block_letter="A")
        eighth_act = EighthActivity.objects.create(name="Test Activity")
        eighth_sched_act = EighthScheduledActivity.objects.create(block=eighth_block, activity=eighth_act)
        eighth_signup = EighthSignup.objects.create(user=user_2021, scheduled_activity=eighth_sched_act, was_absent=True)

        # We must patch timezone.now() to return a 2020 date
        with patch(
            "intranet.apps.dataimport.management.commands.year_cleanup.timezone.now",
            return_value=datetime(2020, 6, 20, tzinfo=pytz.timezone("America/New_York")),
        ) as m:
            call_command("year_cleanup", senior_grad_year=2021, run=True, confirm=True)

        m.assert_called()

        # Check if things changed
        # user_2020 should not exist anymore
        self.assertEqual(0, get_user_model().objects.filter(id=user_2020.id).count())

        # sysadmin_user_2020 should be an alum
        self.assertEqual("alum", get_user_model().objects.get(id=sysadmin_user_2020.id).user_type)

        # The 2021 eighth absence should be archived
        self.assertFalse(EighthSignup.objects.get(id=eighth_signup.id).was_absent)
        self.assertTrue(EighthSignup.objects.get(id=eighth_signup.id).archived_was_absent)

        # 2021 seen_welcome should be False
        self.assertFalse(get_user_model().objects.get(id=user_2021.id).seen_welcome)

        # 2021's admin comments should have been 'archived'
        self.assertIn("=== 2019-2020 comments ===", get_user_model().objects.get(id=user_2021.id).admin_comments)


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

        # Test file input
        file_contents = "Student ID\n11111\n55555"
        with patch("intranet.apps.dataimport.management.commands.delete_users.open", mock_open(read_data=file_contents)) as m:
            call_command("delete_users", filename="foo.csv", header="Student ID", run=True, confirm=True)

        m.assert_called_with("foo.csv", "r")
        with self.assertRaises(get_user_model().DoesNotExist):
            get_user_model().objects.get(username="2021ttester")


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

    def test_command(self):
        # Create a counselor user
        get_user_model().objects.get_or_create(username="abcounselor", user_type="counselor")

        csv_contents = (
            "Last Name,First Name,Middle Name,Student ID,Grade,Gender,Nick Name,Counselor\n"
            "Doe,Jane,Test,2222222,09,F,,abcounselor\n"
            "Doe,John,,1111111,09,M,,abcounselor"
        )

        with patch("intranet.apps.dataimport.management.commands.import_students.open", mock_open(read_data=csv_contents)) as m:
            call_command("import_students", filename="foo.csv", grad_year=2021, run=False)

        m.assert_called_once()

        self.assertEqual(0, get_user_model().objects.filter(username="2021jdoe", first_name="Jane").count())
        self.assertEqual(0, get_user_model().objects.filter(username="2021jdoe1", first_name="John").count())

        with patch("intranet.apps.dataimport.management.commands.import_students.open", mock_open(read_data=csv_contents)) as m:
            call_command("import_students", filename="foo.csv", grad_year=2021, run=True, confirm=True)

        m.assert_called_once()

        self.assertEqual(1, get_user_model().objects.filter(username="2021jdoe", first_name="Jane").count())
        self.assertEqual(1, get_user_model().objects.filter(username="2021jdoe1", first_name="John").count())


class ImportStaffTest(IonTestCase):
    def test_command(self):
        csv_contents = "Username,First Name,Last Name,Middle Name,Gender\njdoe,John,Doe,,M\njdoe1,Jane,Doe,,F"

        with patch("intranet.apps.dataimport.management.commands.import_staff.open", mock_open(read_data=csv_contents)) as m:
            call_command("import_staff", filename="foo.csv", run=True, confirm=True)

        m.assert_called_once()

        self.assertEqual(1, get_user_model().objects.filter(username="jdoe", first_name="John").count())
        self.assertEqual(1, get_user_model().objects.filter(username="jdoe1", first_name="Jane").count())

        # If we try again (create duplicate users), there should not be any duplicate users created
        with patch("intranet.apps.dataimport.management.commands.import_staff.open", mock_open(read_data=csv_contents)) as m:
            call_command("import_staff", filename="foo.csv", run=True, confirm=True)

        m.assert_called_once()

        self.assertEqual(1, get_user_model().objects.filter(username="jdoe", first_name="John").count())
        self.assertEqual(1, get_user_model().objects.filter(username="jdoe1", first_name="Jane").count())


class ImportEighthTest(IonTestCase):
    def test_command(self):
        """This is a stub. You can help us by expanding it."""
        try:
            call_command("import_eighth")
        except CommandError as exception:
            if "data_fname" not in str(exception):
                raise exception


class ImportPhotosTest(IonTestCase):
    def test_command(self):
        """This is a stub. You can help us by expanding it."""
        try:
            call_command("import_photos")
        except CommandError as exception:
            if "directory" not in str(exception):
                raise exception


class ImportUsersTest(IonTestCase):
    def test_command(self):
        """This is a stub. You can help us by expanding it."""
        try:
            call_command("import_users")
        except CommandError as exception:
            if "data_fname" not in str(exception):
                raise exception
