import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..groups.models import Group
from ..users.models import Email
from .exceptions import SignupException
from .models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor
from .notifications import absence_email, signup_status_email


class EighthAbstractTest(IonTestCase):
    def add_block(self, **args):
        # Bypass the manual block creation form.
        args.update({"custom_block": True})
        response = self.client.post(reverse("eighth_admin_add_block"), args)
        self.assertEqual(response.status_code, 302)
        return EighthBlock.objects.get(date=args["date"], block_letter=args["block_letter"])

    def add_room(self, **args):
        response = self.client.post(reverse("eighth_admin_add_room"), args)
        self.assertEqual(response.status_code, 302)
        return EighthRoom.objects.get(name=args["name"])

    def add_activity(self, **args):
        response = self.client.post(reverse("eighth_admin_add_activity"), args)
        self.assertEqual(response.status_code, 302)
        return EighthActivity.objects.get(name=args["name"])


class EighthTest(EighthAbstractTest):
    """
    Tests for the eighth module.
    """

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username="awilliam", graduation_year=get_senior_graduation_year() + 1, id=8889)[0]

    def create_sponsor(self):
        user = get_user_model().objects.get_or_create(username="ateacher", first_name="A", last_name="Teacher", user_type="teacher")[0]
        return user

    def test_sponsor(self):
        sponsor = EighthSponsor.objects.get_or_create(user=self.user, first_name="Eighth", last_name="Sponsor")[0]
        self.assertEqual(sponsor.name, "Sponsor")
        sponsor.show_full_name = True
        self.assertEqual(sponsor.name, "Sponsor, Eighth")
        self.assertEqual(str(sponsor), "Sponsor, Eighth")

    def schedule_activity(self, block_id, activity_id):
        # FIXME: figure out a way to do this that involves less hard-coding.
        args = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "",
            "form-0-block": block_id,
            "form-0-activity": activity_id,
            "form-0-scheduled": True,
            "form-0-capacity": 1,
        }
        response = self.client.post(reverse("eighth_admin_schedule_activity"), args)
        self.assertEqual(response.status_code, 302)
        return EighthScheduledActivity.objects.get(block__id=block_id, activity__id=activity_id)

    def test_add_user(self):
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

    def test_past_activities_listed_properly(self):
        self.make_admin()
        activity = self.add_activity(name="Test Activity 1")

        cur_date = timezone.localtime(timezone.now()).date()
        one_day = datetime.timedelta(days=1)

        past_date_str = (cur_date - one_day).strftime("%Y-%m-%d")
        today_date_str = cur_date.strftime("%Y-%m-%d")
        future_date_str = (cur_date + one_day).strftime("%Y-%m-%d")

        block_past = self.add_block(date=past_date_str, block_letter="A")

        schact_past = self.schedule_activity(block_past.id, activity.id)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [])
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past)])

        block_today = self.add_block(date=today_date_str, block_letter="A")
        block_future = self.add_block(date=future_date_str, block_letter="A")

        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [])
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past)])

        schact_today = self.schedule_activity(block_today.id, activity.id)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_today)])
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past), repr(schact_today)])

        schact_future = self.schedule_activity(block_future.id, activity.id)
        response = self.client.get(reverse("eighth_activity", args=[activity.id]))
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_today), repr(schact_future)])
        response = self.client.get(reverse("eighth_activity", args=[activity.id]), {"show_all": 1})
        self.assertQuerysetEqual(response.context["scheduled_activities"], [repr(schact_past), repr(schact_today), repr(schact_future)])

    def verify_signup(self, user, schact):
        old_count = schact.eighthsignup_set.count()
        schact.add_user(user)
        self.assertEqual(schact.eighthsignup_set.count(), old_count + 1)
        self.assertEqual(user.eighthsignup_set.filter(scheduled_activity__block=schact.block).count(), 1)

    def test_signups(self):
        """Do some sample signups."""

        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year() + 1)
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        self.verify_signup(user1, schact1)

    def test_blacklist(self):
        """Make sure users cannot sign up for blacklisted activities."""

        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year())
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        act1.users_blacklisted.add(user1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        with self.assertRaisesMessage(SignupException, "Blacklist"):
            schact1.add_user(user1)

    def test_all_associated_rooms(self):
        """Make sure EighthScheduledActivities can return all associated rooms."""

        self.make_admin()
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)
        room2 = self.add_room(name="room2", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)
        schact1.rooms.add(room2)

        self.assertQuerysetEqual(schact1.get_all_associated_rooms(), [repr(room1), repr(room2)])

    def test_room_use(self):
        """Make sure EighthScheduledActivities return the correct room."""

        self.make_admin()
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)
        room2 = self.add_room(name="room2", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        self.assertIn(room1, schact1.get_true_rooms())
        self.assertEqual(1, len(schact1.get_true_rooms()))

        schact1.rooms.add(room2)
        self.assertIn(room2, schact1.get_true_rooms())
        self.assertEqual(1, len(schact1.get_true_rooms()))

    def test_room_formatting(self):
        """Make sure a room name formatting is correct."""
        self.make_admin()
        room1 = self.add_room(name="999", capacity=1)
        self.assertEqual("Rm. %s" % room1.name, room1.formatted_name)
        room2 = self.add_room(name="Lab 999", capacity=1)
        self.assertEqual(room2.name, room2.formatted_name)
        room4 = self.add_room(name="Room 999", capacity=1)
        self.assertEqual("Rm. 999", room4.formatted_name)

    def test_both_blocks(self):
        """Make sure that signing up for a both blocks activity works."""
        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year() + 1)
        group1 = Group.objects.create(name="group1")
        user1.groups.add(group1)
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        block2 = self.add_block(date="2015-01-01", block_letter="B")
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        act1.sticky = True
        act1.save()

        schact1 = self.schedule_activity(act1.id, block1.id)

        act2 = self.add_activity(name="Test Activity 2")
        act2.rooms.add(room1)
        act2.both_blocks = True
        act2.save()

        schact2 = self.schedule_activity(act2.id, block2.id)

        self.assertTrue(schact2.is_both_blocks())

        response = self.client.post(reverse("eighth_admin_signup_group_action", args=[group1.id, schact1.id]), {"confirm": True})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("eighth_admin_signup_group_action", args=[group1.id, schact2.id]), {"confirm": True})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("eighth_admin_signup_group_action", args=[group1.id, schact1.id]), {"confirm": True})
        self.assertEqual(response.status_code, 302)

    def test_signup_status_email(self):
        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year() + 1)
        Email.objects.get_or_create(address="awilliam@tjhsst.edu", user=user1)
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        block2 = self.add_block(date="2015-01-01", block_letter="B")
        act1 = self.add_activity(name="Test Activity 1")
        room1 = self.add_room(name="room1", capacity=1)
        act1.rooms.add(room1)

        msg = signup_status_email(user1, [block1, block2], use_celery=False)
        self.assertIn("Jan. 1, 2015 (B): No activity selected", msg.body)
        self.assertIn("Jan. 1, 2015 (A): No activity selected", msg.body)

        sa1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=act1)[0]
        sa1.add_user(user1)

        msg = signup_status_email(user1, [block1, block2], use_celery=False)
        self.assertIn("Jan. 1, 2015 (B): No activity selected", msg.body)
        self.assertNotIn("Jan. 1, 2015 (A): No activity selected", msg.body)

        sa2 = EighthScheduledActivity.objects.get_or_create(block=block2, activity=act1)[0]
        sa2.add_user(user1)

        msg = signup_status_email(user1, [block1, block2], use_celery=False)
        self.assertNotIn("Jan. 1, 2015 (B): No activity selected", msg.body)
        self.assertNotIn("Jan. 1, 2015 (A): No activity selected", msg.body)

    def test_absence_email(self):
        self.make_admin()
        user1 = get_user_model().objects.create(username="user1")
        Email.objects.get_or_create(address="awilliam@tjhsst.edu", user=user1)
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        act1 = self.add_activity(name="Test Activity 1")
        room1 = self.add_room(name="room1", capacity=1)
        act1.rooms.add(room1)

        sa1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=act1)[0]
        sa1.attendance_taken = True
        es1 = EighthSignup.objects.get_or_create(user=user1, was_absent=True, scheduled_activity=sa1)[0]

        msg = absence_email(es1, use_celery=False)
        self.assertIn("Jan. 1, 2015 (A)", msg.body)

    def test_take_attendance_zero(self):
        """ Make sure all activities with zero students are marked as having attendance taken when button is pressed. """
        self.make_admin()
        block1 = self.add_block(date="3000-11-11", block_letter="A")

        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)
        schact1.attendance_taken = False
        schact1.save()

        response = self.client.post(
            reverse("eighth_admin_view_activities_without_attendance") + "?" + urlencode({"block": block1.id}), {"take_attendance_zero": "1"}
        )
        self.assertEqual(response.status_code, 302)

        # Make sure activity is marked as attendance taken.
        self.assertTrue(EighthScheduledActivity.objects.get(id=schact1.id).attendance_taken)

    def test_take_attendance_cancelled(self):
        """ Make sure students in a cancelled activity are marked as absent when the button is pressed. """
        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year() + 1)
        block1 = self.add_block(date="3000-11-11", block_letter="A")

        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)
        schact1.attendance_taken = False

        schact1.add_user(user1)

        schact1.cancelled = True
        schact1.save()

        response = self.client.post(
            reverse("eighth_admin_view_activities_without_attendance") + "?" + urlencode({"block": block1.id}), {"take_attendance_cancelled": "1"}
        )
        self.assertEqual(response.status_code, 302)

        # Make sure attendance has been marked as taken.
        self.assertTrue(EighthScheduledActivity.objects.get(id=schact1.id).attendance_taken)

        # Make sure EighthSignup object has been marked as absent.
        self.assertTrue(EighthSignup.objects.get(user=user1, scheduled_activity=schact1).was_absent)

        # Make sure student has correct number of absences.
        self.assertEqual(get_user_model().objects.get(id=user1.id).absence_count(), 1)

    def test_switch_cancelled_sticky(self):
        """Make sure users can switch out of cancelled activities even if they are stickied in."""
        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year() + 1)

        EighthActivity.objects.all().delete()
        EighthBlock.objects.all().delete()

        block1 = self.add_block(date="3000-11-11", block_letter="A")
        act1 = self.add_activity(name="Test Activity 1")
        schact1 = EighthScheduledActivity.objects.create(activity=act1, block=block1, capacity=1)
        act2 = self.add_activity(name="Test Activity 2")
        schact2 = EighthScheduledActivity.objects.create(activity=act2, block=block1, capacity=1)

        schact1.sticky = True
        schact1.save()

        schact1.add_user(user1)

        self.assertTrue(EighthSignup.objects.filter(scheduled_activity=schact1, user=user1).exists())

        with self.assertRaisesMessage(SignupException, "Sticky"):
            schact2.add_user(user1)

        schact1.cancel()

        schact2.add_user(user1)

        self.assertTrue(EighthSignup.objects.filter(scheduled_activity=schact2, user=user1).exists())

    def test_add_sponsor_form(self):
        # Make sure user not in database is not created
        self.make_admin()
        params = {
            "first_name": "Test",
            "last_name": "User",
            "user": 9001,
            "department": "general",
            "online_attendance": "on",
            "contracted_eighth": "on",
        }

        response = self.client.post(reverse("eighth_admin_add_sponsor"), params, follow=True)
        self.assertEqual(response.status_code, 200)

        # Test that error is raised and redirects
        self.assertTemplateUsed(response, "eighth/admin/add_sponsor.html")

        self.assertFormError(response, "form", "user", "Select a valid choice. {} is not one of the available choices.".format(params["user"]))

        user = self.create_sponsor()
        params = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user": user.pk,
            "department": "general",
            "online_attendance": "on",
            "full_time": "on",
        }

        response = self.client.post(reverse("eighth_admin_add_sponsor"), params, follow=True)
        self.assertEqual(response.status_code, 200)

        # Make sure that new EighthSponsor is created
        self.assertTrue(EighthSponsor.objects.filter(user=user).exists())

    def test_passes(self):
        self.make_admin()
        EighthBlock.objects.all().delete()
        block = self.add_block(date="2015-01-01", block_letter="A")
        act = self.add_activity(name="Test Activity 1")
        schact = self.schedule_activity(act.id, block.id)

        self.assertFalse(schact.has_open_passes())

        schact.add_user(self.user)
        signup1 = EighthSignup.objects.get(scheduled_activity=schact, user=self.user)
        self.assertFalse(signup1.after_deadline)

        self.assertFalse(schact.has_open_passes())

        block.locked = True
        block.save()
        schact.block.refresh_from_db()

        self.assertFalse(schact.has_open_passes())

        schact.add_user(self.user, force=True)
        signup2 = EighthSignup.objects.get(scheduled_activity=schact, user=self.user)
        self.assertTrue(signup2.after_deadline)

        self.assertTrue(schact.has_open_passes())

        signup2.accept_pass()

        self.assertFalse(schact.has_open_passes())

    def test_true_capacity(self):
        self.make_admin()
        block = self.add_block(date="2015-01-01", block_letter="A")
        act = self.add_activity(name="Test Activity 1")
        schact = self.schedule_activity(act.id, block.id)

        room1 = EighthRoom.objects.create(name="Test Room 1", capacity=1)
        room5 = EighthRoom.objects.create(name="Test Room 5", capacity=5)
        room10 = EighthRoom.objects.create(name="Test Room 10", capacity=10)

        schact.capacity = 10
        schact.activity.default_capacity = 0
        self.assertEqual(schact.get_true_capacity(), 10)
        schact.rooms.add(room1)
        self.assertEqual(schact.get_true_capacity(), 10)
        schact.capacity = None
        self.assertEqual(schact.get_true_capacity(), 1)

        schact.rooms.add(room10)
        self.assertEqual(schact.get_true_capacity(), 11)
        schact.rooms.add(room5)
        self.assertEqual(schact.get_true_capacity(), 16)

        schact.rooms.clear()
        self.assertEqual(schact.get_true_capacity(), 0)
        schact.activity.default_capacity = 13
        self.assertEqual(schact.get_true_capacity(), 13)
        schact.rooms.add(room10)
        self.assertEqual(schact.get_true_capacity(), 10)

    def test_total_capacity(self):
        self.make_admin()

        room1 = EighthRoom.objects.create(name="Test Room 1", capacity=1)
        room10 = EighthRoom.objects.create(name="Test Room 10", capacity=10)
        room_inf = EighthRoom.objects.create(name="Large Test Room", capacity=-1)

        self.assertEqual(EighthRoom.total_capacity_of_rooms([]), 0)
        for rm in [room1, room10, room_inf]:
            self.assertEqual(EighthRoom.total_capacity_of_rooms([rm]), rm.capacity)

        self.assertEqual(EighthRoom.total_capacity_of_rooms([room1, room10]), 11)
        self.assertEqual(EighthRoom.total_capacity_of_rooms([room1, room_inf]), -1)
        self.assertEqual(EighthRoom.total_capacity_of_rooms([room_inf, room10]), -1)

    def test_cancel_uncancel(self):
        self.make_admin()
        block = self.add_block(date="2015-01-01", block_letter="A")
        act = self.add_activity(name="Test Activity 1")
        schact = self.schedule_activity(act.id, block.id)

        self.assertFalse(schact.cancelled)
        schact.cancel()
        schact.refresh_from_db()
        self.assertTrue(schact.cancelled)
        schact.uncancel()
        self.assertFalse(schact.cancelled)

    def test_active_schedulings(self):
        today = timezone.localtime().date()
        year_past = today - datetime.timedelta(days=370)
        year_future = today + datetime.timedelta(days=370)

        self.make_admin()
        act = self.add_activity(name="Test Activity 1")

        EighthBlock.objects.all().delete()
        block_past = self.add_block(date=year_past, block_letter="A")
        block_today = self.add_block(date=today, block_letter="A")
        block_future = self.add_block(date=year_future, block_letter="A")

        self.assertQuerysetEqual(act.get_active_schedulings(), [])
        EighthScheduledActivity.objects.create(activity=act, block=block_past)
        self.assertQuerysetEqual(act.get_active_schedulings(), [])
        schact_today = EighthScheduledActivity.objects.create(activity=act, block=block_today)
        self.assertQuerysetEqual(act.get_active_schedulings(), [repr(schact_today)])
        EighthScheduledActivity.objects.create(activity=act, block=block_future)
        self.assertQuerysetEqual(act.get_active_schedulings(), [repr(schact_today)])


class EighthAdminTest(EighthAbstractTest):
    def add_activity(self, **args):
        response = self.client.post(reverse("eighth_admin_add_activity"), args)
        self.assertEqual(response.status_code, 302)
        return EighthActivity.objects.get(name=args["name"])

    def test_eighth_admin_dashboard_view(self):
        user = self.login()
        # Test as non-eighth admin
        response = self.client.get(reverse("eighth_admin_dashboard"))
        self.assertEqual(response.status_code, 302)

        user = self.make_admin()

        for i in range(1, 21):
            self.add_activity(name="Test{}".format(i))
            Group.objects.create(name="Test{}".format(i))
            user = get_user_model().objects.create(username="awilliam{}".format(i))
            EighthRoom.objects.create(name="Test{}".format(i))
            EighthSponsor.objects.create(user=user, first_name="Angela{}".format(i), last_name="William")

        self.add_block(date="9001-4-20", block_letter="A")

        response = self.client.get(reverse("eighth_admin_dashboard"))
        self.assertTemplateUsed(response, "eighth/admin/dashboard.html")

        self.assertEqual(response.context["start_date"], timezone.localdate())
        self.assertQuerysetEqual(response.context["all_activities"], [repr(activity) for activity in EighthActivity.objects.all().order_by("name")])
        self.assertQuerysetEqual(response.context["blocks_after_start_date"], [repr(block) for block in EighthBlock.objects.all()])
        self.assertQuerysetEqual(response.context["groups"], [repr(group) for group in Group.objects.all().order_by("name")])
        self.assertQuerysetEqual(response.context["rooms"], [repr(room) for room in EighthRoom.objects.all()])
        self.assertQuerysetEqual(
            response.context["sponsors"], [repr(sponsor) for sponsor in EighthSponsor.objects.order_by("last_name", "first_name").all()]
        )
        self.assertQuerysetEqual(response.context["blocks_next"], [repr(block) for block in EighthBlock.objects.filter(date="9001-4-20").all()])
        self.assertEqual(response.context["blocks_next_date"], datetime.datetime(9001, 4, 20).date())
        self.assertEqual(response.context["admin_page_title"], "Eighth Period Admin")
        self.assertEqual(response.context["signup_users_count"], get_user_model().objects.get_students().count())


class EighthExceptionTest(IonTestCase):
    def test_signup_exception(self):
        signup_exception = SignupException()
        # Test that response is plain with no errors
        self.assertEqual(signup_exception.as_response()["Content-Type"], "text/plain")

        signup_exception.SignupForbidden = True
        self.assertEqual(len(signup_exception.errors), 1)

        # Test that response is plain with 1 error
        self.assertEqual(signup_exception.as_response()["Content-Type"], "text/plain")

        signup_exception.ScheduledActivityCancelled = True
        self.assertEqual(len(signup_exception.errors), 2)

        # Test SignupException messages
        expected_messages_no_admin = []
        expected_messages_admin = []
        for error in ["ScheduledActivityCancelled", "SignupForbidden"]:
            expected_messages_no_admin.append(SignupException._messages[error][0])  # pylint: disable=protected-access
            expected_messages_admin.append(SignupException._messages[error][1])  # pylint: disable=protected-access
        self.assertEqual(signup_exception.messages(), expected_messages_no_admin)
        self.assertEqual(signup_exception.messages(admin=True), expected_messages_admin)
        response_plain = signup_exception.as_response(html=False)
        self.assertEqual(response_plain.content.decode(), "\n".join(expected_messages_no_admin))
        self.assertEqual(response_plain["Content-Type"], "text/plain")

        # Test string representations
        self.assertEqual(str(signup_exception), "ScheduledActivityCancelled, SignupForbidden")
        self.assertEqual(repr(signup_exception), "SignupException({})".format(str(signup_exception)))
