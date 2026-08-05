from datetime import datetime
from io import StringIO
from unittest.mock import mock_open, patch

import pytz
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ...test.ion_test import IonTestCase
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..users.models import User
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
            f"OK: senior_grad_year = {year + 1}",
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

        m.assert_called_with("foo.csv", encoding="utf-8")
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
        # Create an administrator user, and a counselor who reports to them
        administrator = get_user_model().objects.get_or_create(username="abadmin", user_type="teacher")[0]
        get_user_model().objects.get_or_create(username="abadmin2", user_type="teacher")
        get_user_model().objects.get_or_create(username="abcounselor", user_type="counselor", administrator=administrator)

        # Jane's administrator is named explicitly; John's is blank, so it comes from his counselor
        csv_contents = (
            "Last Name,First Name,Middle Name,Student ID,Grade,Gender,Nick Name,Counselor,Administrator\n"
            "Doe,Jane,Test,2222222,09,F,,abcounselor,abadmin2\n"
            "Doe,John,,1111111,09,M,,abcounselor,"
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

        self.assertEqual("abadmin2", get_user_model().objects.get(username="2021jdoe").administrator.username)
        self.assertEqual("abadmin", get_user_model().objects.get(username="2021jdoe1").administrator.username)


class UpdateAdministratorsTest(IonTestCase):
    def setUp(self) -> None:
        # Two subschool administrators, and a counselor assigned to each
        self.adminone = get_user_model().objects.get_or_create(username="adminone", last_name="AdminOne", user_type="teacher")[0]
        self.admintwo = get_user_model().objects.get_or_create(username="admintwo", last_name="AdminTwo", user_type="teacher")[0]

        self.counselorone = get_user_model().objects.get_or_create(
            username="counselorone", last_name="CounselorOne", user_type="counselor", administrator=self.adminone
        )[0]
        self.counselortwo = get_user_model().objects.get_or_create(
            username="counselortwo", last_name="CounselorTwo", user_type="counselor", administrator=self.admintwo
        )[0]
        # A counselor nobody has assigned an administrator to yet
        self.counselorthree = get_user_model().objects.get_or_create(username="counselorthree", last_name="CounselorThree", user_type="counselor")[0]

    def run_command(self, file_contents: str, *args: str) -> None:
        with patch("intranet.apps.dataimport.management.commands.update_administrators.open", mock_open(read_data=file_contents)):
            call_command("update_administrators", "foo.csv", *args)

    def administrator_of(self, username: str) -> User | None:
        return get_user_model().objects.get(username=username).administrator

    def test_inherits_from_counselor(self) -> None:
        """With no Administrator column at all, every student takes their counselor's administrator."""
        file_contents = "Student ID\n1111111\n2222222\n3333333"

        get_user_model().objects.get_or_create(username="2021atest", student_id=1111111, user_type="student", counselor=self.counselorone)
        get_user_model().objects.get_or_create(username="2021atest2", student_id=2222222, user_type="student", counselor=self.counselortwo)
        # Already correct, so this one should simply be left alone
        get_user_model().objects.get_or_create(
            username="2021atest3", student_id=3333333, user_type="student", counselor=self.counselortwo, administrator=self.admintwo
        )

        # Pretend mode should not change anything
        self.run_command(file_contents)
        self.assertIsNone(self.administrator_of("2021atest"))

        self.run_command(file_contents, "--run")

        self.assertEqual("adminone", self.administrator_of("2021atest").username)
        self.assertEqual("admintwo", self.administrator_of("2021atest2").username)
        self.assertEqual("admintwo", self.administrator_of("2021atest3").username)

    def test_reassigns_when_counselor_changes(self) -> None:
        """A student whose counselor moved subschools follows their counselor's administrator."""
        file_contents = "Student ID,Administrator\n1111111,"

        get_user_model().objects.get_or_create(
            username="2021atest", student_id=1111111, user_type="student", counselor=self.counselorone, administrator=self.admintwo
        )

        self.run_command(file_contents, "--run")

        self.assertEqual("adminone", self.administrator_of("2021atest").username)

    def test_explicit_administrator_wins(self) -> None:
        """An Administrator named in the CSV overrides what the counselor would imply."""
        file_contents = 'Student ID,Administrator\n1111111,AdminTwo\n2222222,"AdminTwo, Alice"'

        get_user_model().objects.get_or_create(username="2021atest", student_id=1111111, user_type="student", counselor=self.counselorone)
        get_user_model().objects.get_or_create(username="2021atest2", student_id=2222222, user_type="student", counselor=self.counselorone)

        self.run_command(file_contents, "--run")

        # Both the bare last name and the SIS "Last, First" form should resolve
        self.assertEqual("admintwo", self.administrator_of("2021atest").username)
        self.assertEqual("admintwo", self.administrator_of("2021atest2").username)

    def test_unresolvable_rows_are_skipped(self) -> None:
        """Rows that cannot be resolved are reported and skipped rather than aborting the run."""
        file_contents = (
            "Student ID,Administrator\n"
            "1111111,NoSuchAdmin\n"  # no staff account by that name
            "2222222,\n"  # counselor has no administrator to inherit
            "3333333,\n"  # no counselor at all
            "4444444,\n"  # no Ion account for this SID
        )

        get_user_model().objects.get_or_create(username="2021atest", student_id=1111111, user_type="student", counselor=self.counselorone)
        get_user_model().objects.get_or_create(username="2021atest2", student_id=2222222, user_type="student", counselor=self.counselorthree)
        get_user_model().objects.get_or_create(username="2021atest3", student_id=3333333, user_type="student")

        self.run_command(file_contents, "--run")

        self.assertIsNone(self.administrator_of("2021atest"))
        self.assertIsNone(self.administrator_of("2021atest2"))
        self.assertIsNone(self.administrator_of("2021atest3"))

    def test_only_teachers_match_a_surname(self) -> None:
        """Administrators are teachers, so no other user type may be matched by surname."""
        for user_type in ("counselor", "user", "alum", "service", "simple_user", "tjstar_presenter", "student"):
            with self.subTest(user_type=user_type):
                get_user_model().objects.filter(last_name="Uniquesurname").delete()
                get_user_model().objects.create(username=f"n{user_type}", last_name="Uniquesurname", user_type=user_type)

                student = get_user_model().objects.update_or_create(
                    username="2021anonstaff", defaults={"student_id": 7777777, "user_type": "student", "administrator": None}
                )[0]

                self.run_command("Student ID,Administrator\n7777777,Uniquesurname", "--run")

                student.refresh_from_db()
                self.assertIsNone(student.administrator)

        # ...while a teacher with that surname does match
        get_user_model().objects.filter(last_name="Uniquesurname").delete()
        teacher = get_user_model().objects.create(username="realteacher", last_name="Uniquesurname", user_type="teacher")

        self.run_command("Student ID,Administrator\n7777777,Uniquesurname", "--run")

        self.assertEqual(teacher, self.administrator_of("2021anonstaff"))

    def test_all_students_from_db(self) -> None:
        """--all runs the counselor chain over every student who has not graduated, with no CSV."""
        senior_year = get_senior_graduation_year()

        get_user_model().objects.get_or_create(
            username="atest", student_id=1111111, user_type="student", counselor=self.counselorone, graduation_year=senior_year
        )
        get_user_model().objects.get_or_create(
            username="atest2", student_id=2222222, user_type="student", counselor=self.counselortwo, graduation_year=senior_year + 1
        )
        # Already graduated, so left alone
        get_user_model().objects.get_or_create(
            username="atest3", student_id=3333333, user_type="student", counselor=self.counselorone, graduation_year=senior_year - 1
        )

        # Pretend mode should not change anything
        call_command("update_administrators", "--all")
        self.assertIsNone(self.administrator_of("atest"))

        call_command("update_administrators", "--all", "--run")

        self.assertEqual("adminone", self.administrator_of("atest").username)
        self.assertEqual("admintwo", self.administrator_of("atest2").username)
        self.assertIsNone(self.administrator_of("atest3"))

    def test_graduation_years_from_db(self) -> None:
        """--graduation-years narrows the run to the given classes."""
        get_user_model().objects.get_or_create(
            username="2027atest", student_id=1111111, user_type="student", counselor=self.counselorone, graduation_year=2027
        )
        get_user_model().objects.get_or_create(
            username="2028atest", student_id=2222222, user_type="student", counselor=self.counselortwo, graduation_year=2028
        )
        get_user_model().objects.get_or_create(
            username="2029atest", student_id=3333333, user_type="student", counselor=self.counselorone, graduation_year=2029
        )

        call_command("update_administrators", "--graduation-years", "2027", "2028", "--run")

        self.assertEqual("adminone", self.administrator_of("2027atest").username)
        self.assertEqual("admintwo", self.administrator_of("2028atest").username)
        self.assertIsNone(self.administrator_of("2029atest"))

    def test_requires_exactly_one_selection(self) -> None:
        """A CSV and a database selection are mutually exclusive, and one of them is required."""
        # Nothing selected
        with self.assertRaises(CommandError):
            call_command("update_administrators", "--run")

        # Both database selections
        with self.assertRaises(CommandError):
            call_command("update_administrators", "--all", "--graduation-years", "2027")

        # A CSV and a database selection
        with self.assertRaises(CommandError):
            call_command("update_administrators", "foo.csv", "--all")


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
