# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Tests for the eighth module.
"""

from django.core.urlresolvers import reverse
from ..eighth.models import EighthBlock, EighthActivity, EighthScheduledActivity
from ..groups.models import Group
from ..users.models import User
from ...test.ion_test import IonTestCase


class EighthTest(IonTestCase):

    def test_add_user(self):
        """
        Tests adding a user to a EighthScheduledActivity.
        """
        # Make user an eighth admin
        user = User.get_user(username='awilliam')
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)

        # password = dankmemes
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            self.client.login(username='awilliam', password='dankmemes')

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
        response = self.client.post(reverse('eighth_admin_schedule_activity'), {'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0', 'form-MAX_NUM_FORMS': '',
                                                                                'form-0-block': block.id, 'form-0-activity': activity.id, 'form-0-scheduled': True, 'form-0-capacity': 1})
        self.assertEqual(response.status_code, 302)

        # Signup for an activity
        response = self.client.post(reverse('eighth_signup'), {'uid': 1337, 'bid': block.id, 'aid': activity.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn(user, EighthScheduledActivity.objects.all()[0].members.all())
