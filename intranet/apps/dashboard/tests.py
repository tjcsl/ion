from datetime import date

from django.contrib.auth import get_user_model

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from .views import gen_schedule, gen_sponsor_schedule


class DashboardTest(IonTestCase):

    """Test for dashboard module"""

    def setUp(self) -> None:
        self.user = get_user_model().objects.get_or_create(
            username="awilliam", graduation_year=get_senior_graduation_year() + 1, user_type="student"
        )[0]

    def test_gen_schedule(self):
        """Tests the gen_schedule method."""
        self.make_admin()

        schedule, no_signup_today = gen_schedule(self.user)

        # There are no eighth blocks and no signups, so this should be None, False
        self.assertIsNone(schedule)
        self.assertFalse(no_signup_today)

        # Add some blocks
        today = date.today()
        block1 = EighthBlock.objects.create(date=today, block_letter="A")
        block2 = EighthBlock.objects.create(date=today, block_letter="B")

        schedule, no_signup_today = gen_schedule(self.user)

        # There are several eighth blocks but no signups, so this should be not None, then True
        self.assertIsNotNone(schedule)
        self.assertTrue(no_signup_today)

        # Add an activity and schedule it
        eighthactivity = EighthActivity.objects.create(name="Testing Ion", description="lol")
        act_block1 = EighthScheduledActivity.objects.create(block=block1, activity=eighthactivity, capacity=10)
        act_block2 = EighthScheduledActivity.objects.create(block=block2, activity=eighthactivity, capacity=10)

        # Sign up this user for block1
        EighthSignup.objects.create(user=self.user, scheduled_activity=act_block1)

        schedule, no_signup_today = gen_schedule(self.user)

        # There are several eighth blocks but no signups, so this should be not None, then True for block2
        self.assertIsNotNone(schedule)
        self.assertTrue(no_signup_today)

        # The first item in `schedule` should be block1 and should be flagged "open"
        self.assertEqual(block1, schedule[0]["block"])
        self.assertEqual("Testing Ion", schedule[0]["current_signup"])
        self.assertIn("open", schedule[0]["flags"])

        # The second item in `schedule` should be block2 and should be flagged "warning" and "open"
        self.assertEqual(block2, schedule[1]["block"])
        self.assertIsNone(schedule[1]["current_signup"])
        self.assertIn("warning", schedule[1]["flags"])
        self.assertIn("open", schedule[1]["flags"])

        # Lock block1 and it should show as locked
        block1.locked = True
        block1.save()

        schedule, no_signup_today = gen_schedule(self.user)
        self.assertIn("locked", schedule[0]["flags"])

        # Sign up for block2, but then cancel the activity
        signup = EighthSignup.objects.create(user=self.user, scheduled_activity=act_block2)
        act_block2.cancel()

        schedule, no_signup_today = gen_schedule(self.user)

        # block2 should show as "warning", "cancelled", and "open"
        for flag in ["warning", "cancelled", "open"]:
            self.assertIn(flag, schedule[1]["flags"])

        # Clean up: remove the blocks, signup, activity, etc.
        block1.delete()
        block2.delete()
        signup.delete()
        act_block2.delete()
        act_block1.delete()

    def test_gen_sponsor_schedule(self):
        """Test cases for the gen_sponsor_schedule method."""
        # Make the user a teacher, and make an EighthSponsor object
        self.user.user_type = "teacher"
        self.user.save()

        sponsor = EighthSponsor.objects.create(first_name="a", last_name="William", user=self.user)

        response = gen_sponsor_schedule(self.user)

        # "sponsor_schedule" should be empty because there are no activities assigned to this sponsor
        self.assertEqual(0, len(response["sponsor_schedule"]))

        # Create two blocks and an activity, scheduled for both
        today = date.today()
        block1 = EighthBlock.objects.create(date=today, block_letter="A")
        block2 = EighthBlock.objects.create(date=today, block_letter="B")
        eighthactivity = EighthActivity.objects.create(name="Testing Ion", description="lol")
        act_block1 = EighthScheduledActivity.objects.create(block=block1, activity=eighthactivity, capacity=10)
        act_block2 = EighthScheduledActivity.objects.create(block=block2, activity=eighthactivity, capacity=10)

        act_block1.sponsors.add(sponsor)
        act_block2.sponsors.add(sponsor)

        response = gen_sponsor_schedule(self.user)

        # "sponsor_schedule" should have two activities because there are two activities assigned to this sponsor
        self.assertEqual(2, len(response["sponsor_schedule"]))

        # num_acts should be two
        self.assertEqual(2, response["num_attendance_acts"])

        # Lock block2, then no_attendance_today should be True
        block2.locked = True
        block2.save()

        response = gen_sponsor_schedule(self.user)

        self.assertTrue(response["num_attendance_acts"])
