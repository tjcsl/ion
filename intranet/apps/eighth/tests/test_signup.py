import json

from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ...schedule.models import Block, Day, DayType, Time
from ..exceptions import SignupException
from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from .eighth_test import EighthAbstractTest


class EighthSignupTest(EighthAbstractTest):
    def test_signup_user_view(self):
        """Tests adding a user to a EighthScheduledActivity."""

        user = self.make_admin()
        # Ensure we can see the user's signed-up activities.
        response = self.client.get(reverse("eighth_signup"))
        self.assertEqual(response.status_code, 200)

        # Create a block
        block = self.add_block(date="9001-4-20", block_letter="A")
        self.assertEqual(block.formatted_date, "Mon, April 20, 9001")

        # Create an activity
        activity = self.add_activity(name="Meme Club")

        # Schedule an activity
        schact = self.schedule_activity(block.id, activity.id)

        # Signup for an activity
        response = self.client.post(reverse("eighth_signup"), {"uid": 8889, "bid": block.id, "aid": activity.id})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("eighth_signup"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(user, schact.members.all())

    def test_add_user_method(self):
        """Tests the EighthScheduledActivity add_user() method."""

        request = RequestFactory().post("/")
        request.user = get_user_model().objects.create(username="user_not_admin")

        self.make_admin()

        user = get_user_model().objects.create(username="user", graduation_year=get_senior_graduation_year() - 1)

        # Create two blocks
        blockA = self.add_block(date="9001-4-20", block_letter="A")
        self.assertEqual(blockA.formatted_date, "Mon, April 20, 9001")

        # Create an activity
        activity = self.add_activity(name="Club")

        # Schedule activity
        schactA = EighthScheduledActivity.objects.create(block=blockA, activity=activity, capacity=1)

        # Attempt to make a request from user_not_admin to signup user (this should fail)
        with self.assertRaisesMessage(SignupException, "SignupForbidden"):
            schactA.add_user(user, request=request, force=False)
        self.assertNotIn(user, schactA.members.all())

        # Add user with grade 13 to schactA (this should fail)
        with self.assertRaisesMessage(SignupException, "SignupForbidden"):
            schactA.add_user(user, request=None, force=False)

        user.graduation_year = get_senior_graduation_year()
        user.save()

        # Add user to a deleted activity (this should fail)
        activity.deleted = True
        activity.save()

        with self.assertRaisesMessage(SignupException, "ActivityDeleted"):
            schactA.add_user(user, request=None, force=False)

        activity.deleted = False
        activity.save()

        # Add user to a locked block (this should fail)
        blockA.locked = True
        blockA.save()

        with self.assertRaisesMessage(SignupException, "BlockLocked"):
            schactA.add_user(user, request=None, force=False)

        blockA.locked = False
        blockA.save()

        # Add user to a cancelled activity (this should fail)
        schactA.cancel()

        with self.assertRaisesMessage(SignupException, "ScheduledActivityCancelled"):
            schactA.add_user(user, request=None, force=False)

        schactA.uncancel()

        # Add user to a full activity (this should fail)
        schactA.capacity = 0
        schactA.save()

        with self.assertRaisesMessage(SignupException, "ActivityFull"):
            schactA.add_user(user, request=None, force=False)

        schactA.capacity = 1
        schactA.save()

        # Add user to an activity with 48 hour presign before 48 hours (this should fail)
        activity.presign = True
        activity.save()

        with self.assertRaisesMessage(SignupException, "Presign"):
            schactA.add_user(user, request=None, force=False)

        activity.presign = False
        activity.save()

        # Add user to an activity that they aren't on the restricted list for (this should fail)
        activity.restricted = True
        activity.save()

        with self.assertRaisesMessage(SignupException, "Restricted"):
            schactA.add_user(user, request=None, force=False)

        activity.restricted = False
        activity.save()

        # Add user to an activity
        schactA.add_user(user, request=None, force=False)
        self.assertIn(user, schactA.members.all())

        # Create a new block and schedule activity
        blockB = self.add_block(date="9001-4-20", block_letter="B")
        schactB = EighthScheduledActivity.objects.create(block=blockB, activity=activity, both_blocks=True, capacity=1)

        # Create a new activity and schedule it during blockA and blockB
        new_activity = self.add_activity(name="New Club")
        new_schactA = EighthScheduledActivity.objects.create(block=blockA, activity=new_activity, capacity=1)
        new_schactB = EighthScheduledActivity.objects.create(block=blockB, activity=new_activity, capacity=1)

        # Switch user to a new activity
        new_schactA.add_user(user, request=None, force=False)
        self.assertIn(user, new_schactA.members.all())
        self.assertNotIn(user, schactA.members.all())

        # Add user to a second one-a-day activity (this should fail)
        new_activity.one_a_day = True
        new_activity.save()

        with self.assertRaisesMessage(SignupException, "OneADay"):
            new_schactB.add_user(user, request=None, force=False)
        self.assertNotIn(user, new_schactB.members.all())

        new_activity.one_a_day = False
        new_activity.save()

        # Switch user into a both_block activity
        schactA.both_blocks = True
        schactA.save()

        schactA.add_user(user, request=None, force=False)
        self.assertIn(user, schactA.members.all())
        self.assertIn(user, schactB.members.all())

        # Switch user out of both_block activity
        new_schactA.add_user(user, request=None, force=False)
        self.assertIn(user, new_schactA.members.all())
        self.assertNotIn(user, schactA.members.all())
        self.assertNotIn(user, schactB.members.all())

    def test_signup_restricitons(self):
        """Make sure users can't sign up for restricted activities or switch out of sticky activities."""
        self.make_admin()
        get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year())
        user2 = get_user_model().objects.create(username="user2", graduation_year=get_senior_graduation_year())
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1", sticky=True, restricted=True, users_allowed=[user2])
        act1.rooms.add(room1)
        schact1 = EighthScheduledActivity.objects.create(block=block1, activity=act1, capacity=5)

        act2 = self.add_activity(name="Test Activity 2")
        act2.rooms.add(room1)
        EighthScheduledActivity.objects.create(block=block1, activity=act2, capacity=5)

        # Ensure that user1 can't sign up for act1
        self.client.post(reverse("eighth_signup", args=[block1.id]), {"aid": act1.id})
        self.assertEqual(len(EighthScheduledActivity.objects.get(block=block1.id, activity=act1.id).members.all()), 0)

        # Ensure that user2 can sign up for act1
        self.verify_signup(user2, schact1)

        # Now that user2 is signed up for act1, make sure they can't switch themselves out
        self.client.post(reverse("eighth_signup", args=[block1.id]), {"aid": act2.id})
        self.assertEqual(len(EighthScheduledActivity.objects.get(block=block1.id, activity=act1.id).members.all()), 1)
        self.assertEqual(len(EighthScheduledActivity.objects.get(block=block1.id, activity=act2.id).members.all()), 0)

    def test_eighth_signup_view(self):
        """Tests :func:`~intranet.apps.eighth.views.signup.eighth_signup_view`."""

        # First, log in as a student
        get_user_model().objects.all().delete()
        user = self.login("2021awilliam")
        user.user_type = "student"
        user.graduation_year = get_senior_graduation_year()
        user.save()

        # Load the page.
        # response = self.client.get(reverse("eighth_signup"))
        # self.assertEqual(200, response.status_code)

        # Create an activity, schedule it, and attempt to sign up.
        today = timezone.localtime().date()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        EighthBlock.objects.get_or_create(date=today, block_letter="B")
        activity = EighthActivity.objects.get_or_create(name="Test Activity", default_capacity=5)[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity, capacity=5)[0]

        response = self.client.post(reverse("eighth_signup"), data={"uid": user.id, "bid": block1.id, "aid": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, EighthSignup.objects.filter(user=user, scheduled_activity=scheduled1).count())

        # Test unsignup
        self.make_admin()
        response = self.client.post(reverse("eighth_signup"), data={"uid": user.id, "bid": block1.id, "unsignup": "unsignup"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, EighthSignup.objects.filter(user=user, scheduled_activity=scheduled1).count())
        response = self.client.post(reverse("eighth_signup"), data={"uid": user.id, "bid": block1.id, "unsignup": "unsignup"})
        self.assertEqual(200, response.status_code)
        self.assertEqual("The signup did not exist.", response.content.decode("UTF-8"))

        # Test the "block" GET parameter
        response = self.client.get(reverse("eighth_signup"), data={"block": block1.id})
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_signup", kwargs={"block_id": block1.id}), response.url)

        response = self.client.get(reverse("eighth_signup"), data={"block": block1.id, "user": user.id})
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_signup", kwargs={"block_id": block1.id}) + f"?user={user.id}", response.url)

    def test_eighth_multi_signup_view(self):
        """Tests :func:`~intranet.apps.eighth.views.signup.eighth_multi_signup_view`."""

        # First, log in as a student
        get_user_model().objects.all().delete()
        user = self.login("2021awilliam")
        user.user_type = "student"
        user.graduation_year = get_senior_graduation_year()
        user.save()

        # Load the page.
        response = self.client.get(reverse("eighth_multi_signup"))
        self.assertEqual(200, response.status_code)

        # Add some blocks and schedule activities
        today = timezone.localtime().date()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        block2 = EighthBlock.objects.get_or_create(date=today, block_letter="B")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity", default_capacity=5)[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity, capacity=5)[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block2, activity=activity, capacity=5)[0]

        # Load the page.
        response = self.client.get(reverse("eighth_multi_signup"), data={"block": [block1.id, block2.id]})
        self.assertEqual(200, response.status_code)
        self.assertEqual([block1, block2], list(response.context["blocks"]))

        # Parse the JSON in `response.context["activities_list"]`
        act_list = json.loads(str(response.context["activities_list"]).encode().decode("unicode-escape"))
        self.assertEqual(1, len(act_list))  # There is one activity
        self.assertEqual(block1.id, act_list["1"]["blocks"][0]["id"])
        self.assertEqual(block2.id, act_list["1"]["blocks"][1]["id"])

        # Try signing this user up for that activity on both blocks
        self.make_admin()
        response = self.client.post(reverse("eighth_multi_signup"), data={"bid": f"{block1.id},{block2.id}", "uid": user.id, "aid": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, EighthSignup.objects.filter(user=user, scheduled_activity=scheduled2).count())
        self.assertEqual(1, EighthSignup.objects.filter(user=user, scheduled_activity=scheduled1).count())

    def test_toggle_favorite_view(self):
        """Tests :func:`~intranet.apps.eighth.views.signup.toggle_favorite_view`."""

        # Add an activity and log in
        user = self.login()
        activity = EighthActivity.objects.get_or_create(name="Test Activity", default_capacity=5)[0]

        # Try to favorite that activity
        response = self.client.post(reverse("eighth_toggle_favorite"), data={"aid": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertIn(user, EighthActivity.objects.get(id=activity.id).favorites.all())

        # Now, unfavorite that activity
        response = self.client.post(reverse("eighth_toggle_favorite"), data={"aid": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertNotIn(user, EighthActivity.objects.get(id=activity.id).favorites.all())

        # Test some invalid parameters
        response = self.client.get(reverse("eighth_toggle_favorite"), data={"aid": activity.id})
        self.assertEqual(405, response.status_code)

        response = self.client.post(reverse("eighth_toggle_favorite"), data={"aid": activity.name})
        self.assertEqual(400, response.status_code)

    def test_eighth_location_view(self):
        """Tests :func:`~intranet.apps.eighth.views.signup.eighth_location`."""

        user = self.make_admin()
        now = timezone.localtime()
        time_start = Time.objects.create(hour=now.time().hour, minute=now.time().minute)
        time_end = Time.objects.create(hour=(now + timezone.timedelta(hours=1)).hour, minute=now.time().minute)
        block = Block.objects.create(name="8A", start=time_start, end=time_end, order=1)
        red_day = DayType.objects.create(name="red")
        red_day.blocks.add(block)
        Day.objects.create(date=now.today(), day_type=red_day)
        # This part is a little hacky. We can't get the location of a response without redirecting, so we:

        # first test that the redirect works
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("eighth_location"))

        # then allow client to follow the redirect in order to add the "seen_eighth_location" cookie
        response = self.client.get("/", follow=True)
        self.assertEqual(200, response.status_code)

        # finally ensure that the "seen_eighth_location" cookie now prevents the redirect
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # Now, add some EighthBlocks and test the view
        EighthBlock.objects.all().delete()
        today = timezone.localtime().date()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        block2 = EighthBlock.objects.get_or_create(date=today, block_letter="B")[0]

        response = self.client.get(reverse("eighth_location"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([[block1, None], [block2, None]], response.context["sch_acts"])

        # Add an activity and a signup
        activity = EighthActivity.objects.get_or_create(name="Test Activity", default_capacity=5)[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=activity, capacity=5)[0]
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled1)

        response = self.client.get(reverse("eighth_location"))
        self.assertEqual(200, response.status_code)

        # The empty strings are because there are no rooms nor sponsors assigned
        self.assertEqual([[block1, scheduled1, "", ""], [block2, None]], response.context["sch_acts"])
