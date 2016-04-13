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
