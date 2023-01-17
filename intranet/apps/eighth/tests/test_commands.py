import csv
import datetime
from io import StringIO
from unittest.mock import mock_open, patch

import pytz

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ...groups.models import Group
from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from .eighth_test import EighthAbstractTest


class EighthCommandsTest(EighthAbstractTest):
    def test_update_counselor(self):
        file_contents = "Student ID,Counselor\n12345,CounselorOne\n54321,CounselorTwo\n55555,CounselorOne"

        # Make some counselors
        get_user_model().objects.get_or_create(username="counselorone", last_name="CounselorOne", user_type="counselor")
        counselortwo = get_user_model().objects.get_or_create(username="counselortwo", last_name="CounselorTwo", user_type="counselor")[0]

        # Make some users
        get_user_model().objects.get_or_create(username="2021ttest", student_id=12345, user_type="student", counselor=counselortwo)
        get_user_model().objects.get_or_create(username="2021ttest2", student_id=54321, user_type="student", counselor=counselortwo)
        get_user_model().objects.get_or_create(username="2021ttester", student_id=55555, user_type="student")

        # Run command
        with patch("intranet.apps.eighth.management.commands.update_counselors.open", mock_open(read_data=file_contents)):
            call_command("update_counselors", "foo.csv", "--run")

        self.assertEqual("counselorone", get_user_model().objects.get(username="2021ttest").counselor.username)
        self.assertEqual("counselortwo", get_user_model().objects.get(username="2021ttest2").counselor.username)
        self.assertEqual("counselorone", get_user_model().objects.get(username="2021ttester").counselor.username)

    def test_absence_email(self):
        """Tests the absence_email command."""

        # Make a user, block, activity, and an absent signup
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled, was_absent=True)

        # Run command
        with patch("intranet.apps.eighth.management.commands.absence_email.absence_email", return_value=None) as m:
            call_command("absence_email")

        m.assert_called_once_with(signup)
        self.assertTrue(EighthSignup.objects.get(id=signup.id).absence_emailed)

        signup = EighthSignup.objects.get(id=signup.id)
        signup.absence_emailed = False
        signup.save()

        with patch("intranet.apps.eighth.management.commands.absence_email.absence_email", return_value=None) as m:
            call_command("absence_email", "--pretend")

        m.assert_not_called()
        self.assertFalse(EighthSignup.objects.get(id=signup.id).absence_emailed)

        with patch("intranet.apps.eighth.management.commands.absence_email.absence_email", return_value=None) as m:
            call_command("absence_email", "--silent")

        m.assert_called_once_with(signup)
        self.assertTrue(EighthSignup.objects.get(id=signup.id).absence_emailed)

    def test_dev_create_blocks(self):
        """Tests the dev_create_blocks command."""

        EighthBlock.objects.all().delete()
        EighthActivity.objects.all().delete()

        activity1 = EighthActivity.objects.get_or_create(name="Test Activity 1", wed_a=True)[0]
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2", wed_b=True)[0]
        activity3 = EighthActivity.objects.get_or_create(name="Test Activity 3", fri_a=True)[0]

        # Controlling the date here
        with patch(
            "intranet.apps.eighth.management.commands.dev_create_blocks.now",
            return_value=datetime.datetime(2021, 3, 28, 10, 0, 0, tzinfo=pytz.timezone("America/New_York")),
        ) as m:
            call_command("dev_create_blocks", "04/04/2021")

        m.assert_called()

        self.assertEqual(4, EighthBlock.objects.all().count())
        self.assertEqual(1, EighthBlock.objects.filter(date="2021-03-31", block_letter="A").count())
        self.assertEqual(1, EighthBlock.objects.filter(date="2021-03-31", block_letter="B").count())
        self.assertEqual(1, EighthBlock.objects.filter(date="2021-04-02", block_letter="A").count())
        self.assertEqual(1, EighthBlock.objects.filter(date="2021-04-02", block_letter="B").count())

        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity1, block__date="2021-03-31", block__block_letter="A").count())
        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity2, block__date="2021-03-31", block__block_letter="B").count())
        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity3, block__date="2021-04-02", block__block_letter="A").count())

        activity3.fri_b = True
        activity3.save()

        with patch(
            "intranet.apps.eighth.management.commands.dev_create_blocks.now",
            return_value=datetime.datetime(2021, 3, 28, 10, 0, 0, tzinfo=pytz.timezone("America/New_York")),
        ) as m:
            call_command("dev_create_blocks", "04/04/2021")

        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity1, block__date="2021-03-31", block__block_letter="A").count())
        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity2, block__date="2021-03-31", block__block_letter="B").count())
        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity3, block__date="2021-04-02", block__block_letter="A").count())
        self.assertEqual(1, EighthScheduledActivity.objects.filter(activity=activity3, block__date="2021-04-02", block__block_letter="B").count())

    def test_delete_duplicate_signups(self):
        """Tests the delete duplicate signups command."""

        # I can't really create a duplicate signup, but I can test to make sure that
        # this command doesn't remove singular signups

        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled)

        call_command("delete_duplicate_signups")

        self.assertEqual(1, EighthSignup.objects.filter(id=signup.id).count())

    def test_dev_generate_signups(self):
        """Tests the dev_generate_signups command."""

        # First, call this command with nothing set up.
        get_user_model().objects.all().delete()
        EighthBlock.objects.all().delete()
        EighthActivity.objects.all().delete()

        today = timezone.localtime() - datetime.timedelta(days=2)

        with patch("intranet.apps.eighth.management.commands.dev_generate_signups.input", return_value="y") as m:
            with self.assertRaises(CommandError):
                call_command("dev_generate_signups", today.strftime("%m/%d/%Y"))

        m.assert_called_once()

        # Create some blocks and activities, and schedule them
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity1, capacity=5)[0]

        block2 = EighthBlock.objects.get_or_create(date=today, block_letter="B")[0]
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block2, activity=activity2, capacity=5)[0]

        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]

        # Call the command
        with patch("intranet.apps.eighth.management.commands.dev_generate_signups.input", return_value="y") as m:
            call_command("dev_generate_signups", today.strftime("%m/%d/%Y"))

        m.assert_called_once()

        self.assertEqual(2, EighthSignup.objects.filter(user=user, scheduled_activity__in=[scheduled2, scheduled1]).count())

    def test_find_duplicates(self):
        """Tests the find duplicates command."""

        EighthSignup.objects.all().delete()

        # Just run the command.
        out = StringIO()
        call_command("find_duplicates", stdout=out)
        self.assertIn("No duplicate signups found", out.getvalue())

        # Add a user with a signup
        today = timezone.localtime()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity1, capacity=5)[0]
        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled1)

        out = StringIO()
        call_command("find_duplicates", stdout=out)
        self.assertIn("No duplicate signups found", out.getvalue())

    def test_generate_similarities(self):
        """Tests the generate_similarities command."""
        # This is a stub. You can help us by expanding it.

        # Just run it
        call_command("generate_similarities")

        # Add an activity
        EighthActivity.objects.get_or_create(name="Test Activity")

        call_command("generate_similarities")

    def test_generate_statistics(self):
        """Tests the generate_statistics command."""

        m = mock_open()
        with patch("intranet.apps.eighth.management.commands.generate_statistics.open", m):
            call_command("generate_statistics")

        m().write.assert_called_once()

    def test_remove_withdrawn_students(self):
        """Tests the remove_withdrawn_students command."""

        Group.objects.all().delete()

        # Call the command - it should error because the "Withdrawn from TJ" group doesn't exist
        out = StringIO()
        call_command("remove_withdrawn_students", stdout=out)
        self.assertIn("Withdrawn group could not be found", out.getvalue())

        # Add a group with no students
        group = Group.objects.create(name="Withdrawn from TJ", id=9)
        out = StringIO()
        call_command("remove_withdrawn_students", stdout=out)
        self.assertIn("No users found in withdrawn group", out.getvalue())

        # Add a user to that group
        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        user.groups.add(group)
        user.save()

        out = StringIO()
        call_command("remove_withdrawn_students", stdout=out)
        self.assertIn("Deleting 2021awilliam", out.getvalue())

        self.assertEqual(0, get_user_model().objects.filter(username="2021awilliam").count())

    def test_signup_statistics(self):
        """Tests the signup_statistics command."""

        # Add an activity but no signups
        today = timezone.localtime()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity1, capacity=5)[0]

        # Run the command
        out = StringIO()
        call_command("signup_statistics", activity1.id, stdout=out)

        reader = csv.DictReader(out.getvalue().splitlines())
        reader_contents = list(reader)
        self.assertEqual(0, len(reader_contents))

        # Add a signup
        user = get_user_model().objects.get_or_create(
            username="2021awilliam",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
            last_name="William",
            first_name="Angela",
        )[0]
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled1)

        # Run the command
        out = StringIO()
        call_command("signup_statistics", activity1.id, stdout=out)

        reader = csv.DictReader(out.getvalue().splitlines())
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual([{"TJ Username": "2021awilliam", "First Name": "Angela", "Last Name": "William", "Number of Signups": "1"}], reader_contents)

    def test_signup_status_email(self):
        """Tests the signup_status_email command."""

        EighthBlock.objects.all().delete()
        get_user_model().objects.all().delete()

        # Running the command should error with "No upcoming blocks"
        out = StringIO()
        call_command("signup_status_email", stdout=out)
        self.assertIn("No upcoming blocks", out.getvalue())

        # Make an EighthBlock
        today = timezone.localtime()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]

        with patch("intranet.apps.eighth.management.commands.signup_status_email.signup_status_email") as m:
            call_command("signup_status_email")
        m.assert_not_called()

        # Make a user but don't sign that user up
        user = get_user_model().objects.get_or_create(
            username="2021awilliam",
            graduation_year=get_senior_graduation_year(),
            user_type="student",
            last_name="William",
            first_name="Angela",
        )[0]

        with patch("intranet.apps.eighth.management.commands.signup_status_email.signup_status_email") as m:
            call_command("signup_status_email", "--everyone")

        m.assert_called_once()

        # Sign this user up for an activity
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity1, capacity=5)[0]
        EighthSignup.objects.create(scheduled_activity=scheduled1, user=user)

        with patch("intranet.apps.eighth.management.commands.signup_status_email.signup_status_email") as m:
            call_command("signup_status_email", "--everyone")

        m.assert_not_called()

        # Cancel that activity
        scheduled1.cancel()

        with patch("intranet.apps.eighth.management.commands.signup_status_email.signup_status_email") as m:
            call_command("signup_status_email", "--everyone")

        m.assert_called_once()
