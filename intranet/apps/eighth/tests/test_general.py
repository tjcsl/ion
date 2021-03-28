import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ....utils.date import get_senior_graduation_year
from ...groups.models import Group
from ...users.models import Email
from ..exceptions import SignupException
from ..models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor
from ..notifications import absence_email, signup_status_email
from .eighth_test import EighthAbstractTest


class EighthTest(EighthAbstractTest):
    """
    Tests for the eighth module.
    """

    def test_sponsor(self):
        sponsor = EighthSponsor.objects.get_or_create(user=self.user, first_name="Eighth", last_name="Sponsor")[0]
        self.assertEqual(sponsor.name, "Sponsor")
        sponsor.show_full_name = True
        self.assertEqual(sponsor.name, "Sponsor, Eighth")
        self.assertEqual(str(sponsor), "Sponsor, Eighth")

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
        self.assertIn("Jan. 1, 2015 (B): No activity selected", msg[0].body)
        self.assertIn("Jan. 1, 2015 (A): No activity selected", msg[0].body)
        self.assertEqual(len(msg), 1)

        sa1 = EighthScheduledActivity.objects.get_or_create(block=block1, activity=act1)[0]
        sa1.add_user(user1)

        msg = signup_status_email(user1, [block1, block2], use_celery=False)
        self.assertIn("Jan. 1, 2015 (B): No activity selected", msg[0].body)
        self.assertNotIn("Jan. 1, 2015 (A): No activity selected", msg[0].body)
        self.assertEqual(len(msg), 1)

        sa2 = EighthScheduledActivity.objects.get_or_create(block=block2, activity=act1)[0]
        sa2.add_user(user1)

        msg = signup_status_email(user1, [block1, block2], use_celery=False)
        self.assertNotIn("Jan. 1, 2015 (B): No activity selected", msg[0].body)
        self.assertNotIn("Jan. 1, 2015 (A): No activity selected", msg[0].body)
        self.assertEqual(len(msg), 1)

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
        self.assertIn("Jan. 1, 2015 (A)", msg[0].body)
        self.assertEqual(len(msg), 1)

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
