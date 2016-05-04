# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

from ..eighth.exceptions import SignupException
from ..eighth.models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity
from ..groups.models import Group
from ..users.models import User
from ...test.ion_test import IonTestCase
"""
Tests for the eighth module.
"""


class EighthTest(IonTestCase):

    def test_add_user(self):
        """Tests adding a user to a EighthScheduledActivity."""
        self.login()
        # Make user an eighth admin
        user = User.get_user(username='awilliam')
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)
        # Ensure we can see the user's signed-up activities.
        response = self.client.get(reverse('eighth_signup'))
        self.assertEqual(response.status_code, 200)

        # Create a block
        response = self.client.post(reverse('eighth_admin_add_block'), {'date': '9001-4-20', 'block_letter': 'A', 'custom_block': True})
        self.assertEqual(response.status_code, 302)
        block = EighthBlock.objects.get_first_upcoming_block()
        self.assertEqual(block.formatted_date, 'Mon, April 20, 9001')

        # Create an activity
        response = self.client.post(reverse('eighth_admin_add_activity'), {'name': 'Meme Club'})
        self.assertEqual(response.status_code, 302)
        activity = EighthActivity.objects.all()[0]

        # Schedule an activity
        # FIXME: figure out a way to do this that involves less hard-coding.
        response = self.client.post(
            reverse('eighth_admin_schedule_activity'), {'form-TOTAL_FORMS': '1',
                                                        'form-INITIAL_FORMS': '0',
                                                        'form-MAX_NUM_FORMS': '',
                                                        'form-0-block': block.id,
                                                        'form-0-activity': activity.id,
                                                        'form-0-scheduled': True,
                                                        'form-0-capacity': 1})
        self.assertEqual(response.status_code, 302)

        # Signup for an activity
        response = self.client.post(reverse('eighth_signup'), {'uid': 1337, 'bid': block.id, 'aid': activity.id})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('eighth_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(user, EighthScheduledActivity.objects.all()[0].members.all())

    def verify_signup(self, user, schact):
        old_count = (schact.eighthsignup_set.count())
        schact.add_user(user)
        self.assertEqual((schact.eighthsignup_set.count()), old_count + 1)
        self.assertEqual((user.eighthsignup_set.filter(scheduled_activity__block=schact.block).count()), 1)

    def test_signups(self):
        """Do some sample signups."""

        user1 = User.objects.create(username="user1")
        block1 = EighthBlock.objects.create(date='2015-01-01', block_letter="A")
        room1 = EighthRoom.objects.create(name="room1")

        act1 = EighthActivity.objects.create(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = EighthScheduledActivity.objects.create(activity=act1, block=block1)

        self.verify_signup(user1, schact1)

    def test_blacklist(self):
        """Make sure users cannot sign up for blacklisted activities."""

        user1 = User.objects.create(username="user1")
        block1 = EighthBlock.objects.create(date='2015-01-01', block_letter="A")
        room1 = EighthRoom.objects.create(name="room1")

        act1 = EighthActivity.objects.create(name="Test Activity 1")
        act1.rooms.add(room1)
        act1.users_blacklisted.add(user1)
        schact1 = EighthScheduledActivity.objects.create(activity=act1, block=block1)

        with self.assertRaisesMessage(SignupException, "Blacklist"):
            schact1.add_user(user1)

    def test_all_associated_rooms(self):
        """Make sure EighthScheduledActivities can return all associated rooms"""

        block1 = EighthBlock.objects.create(date='2015-01-01', block_letter="A")
        room1 = EighthRoom.objects.create(name="room1")
        room2 = EighthRoom.objects.create(name="room2")

        act1 = EighthActivity.objects.create(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = EighthScheduledActivity.objects.create(activity=act1, block=block1)
        schact1.rooms.add(room2)

        self.assertIn(room1, schact1.all_associated_rooms)
        self.assertIn(room2, schact1.all_associated_rooms)
        self.assertEqual(2, len(schact1.all_associated_rooms))

    def test_room_use(self):
        """Make sure EighthScheduledActivities return the correct room"""

        block1 = EighthBlock.objects.create(date='2015-01-01', block_letter="A")
        room1 = EighthRoom.objects.create(name="room1")
        room2 = EighthRoom.objects.create(name="room2")

        act1 = EighthActivity.objects.create(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = EighthScheduledActivity.objects.create(activity=act1, block=block1)

        self.assertIn(room1, schact1.get_scheduled_rooms())
        self.assertEqual(1, len(schact1.get_scheduled_rooms()))

        schact1.rooms.add(room2)
        self.assertIn(room2, schact1.get_scheduled_rooms())
        self.assertEqual(1, len(schact1.get_scheduled_rooms()))

    def test_room_formatting(self):
        """Make sure a room name formatting is correct"""
        room1 = EighthRoom.objects.create(name="999")
        self.assertEqual('Rm. '+room1.name, room1.formatted_name)
        room2 = EighthRoom.objects.create(name="Lab 999")
        self.assertEqual(room2.name, room2.formatted_name)
        room3 = EighthRoom.objects.create(name="Weyanoke 999")
        self.assertEqual('Wey. 999', room3.formatted_name)
        room4 = EighthRoom.objects.create(name="Room 999")
        self.assertEqual('Rm. 999', room4.formatted_name)
