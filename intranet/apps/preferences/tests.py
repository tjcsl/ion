# -*- coding: utf-8 -*-
from django.conf import settings
from django.urls import reverse

from ..users.models import User
from ...test.ion_test import IonTestCase


class PreferencesTest(IonTestCase):

    def setUp(self):
        User.objects.get_or_create(username="awilliam", id="99999", graduation_year=settings.SENIOR_GRADUATION_YEAR + 1)

    def test_get_preferences(self):
        self.login()
        response = self.client.get(reverse('preferences'))
        self.assertEqual(response.status_code, 200)

    def test_set_preferences(self):
        self.login()
        settings_dict = {
            'pf-TOTAL_FORMS': ['1'],
            'ef-0-user': ['99999'],
            'pf-0-number': ['555-555-5555'],
            'wf-INITIAL_FORMS': ['0'],
            'pf-0-id': [''],
            'wf-MAX_NUM_FORMS': ['1000'],
            'ef-MIN_NUM_FORMS': ['0'],
            'wf-TOTAL_FORMS': ['1'],
            'ef-TOTAL_FORMS': ['1'],
            'wf-MIN_NUM_FORMS': ['0'],
            'pf-MIN_NUM_FORMS': ['0'],
            'pf-INITIAL_FORMS': ['0'],
            'ef-0-id': [''],
            'preferred_photo': ['AUTO'],
            'ef-0-address': ['awilliam@tjhsst.edu'],
            'show_pictures-self': ['on'],
            'ef-INITIAL_FORMS': ['0'],
            'pf-0-purpose': ['h'],
            'ef-MAX_NUM_FORMS': ['1000'],
            'receive_push_notifications': ['on'],
            'wf-0-url': ['http://ion.tjhsst.edu/logout'],
            'wf-0-id': [''],
            'pf-0-user': ['99999'],
            'wf-0-user': ['99999'],
            'pf-MAX_NUM_FORMS': ['1000'],
            'show_pictures': ['on']
        }
        response = self.client.post(reverse('preferences'), settings_dict)
        self.assertEqual(response.status_code, 302)

    def test_clear_preferences(self):
        self.login()
        pref_dict = {
            'pf-1-number': [''],
            'pf-1-id': [''],
            'pf-0-number': ['555-555-5555'],
            'pf-0-id': ['12'],
            'wf-MAX_NUM_FORMS': ['1000'],
            'ef-MIN_NUM_FORMS': ['0'],
            'wf-TOTAL_FORMS': ['2'],
            'wf-MIN_NUM_FORMS': ['0'],
            'pf-1-purpose': ['o'],
            'wf-0-id': ['4'],
            'pf-TOTAL_FORMS': ['2'],
            'wf-0-url': ['http://ion.tjhsst.edu/logout'],
            'wf-1-user': ['99999'],
            'pf-0-DELETE': ['on'],
            'ef-1-id': [''],
            'wf-0-DELETE': ['on'],
            'pf-MAX_NUM_FORMS': ['1000'],
            'wf-0-user': ['99999'],
            'ef-1-address': [''],
            'ef-0-user': ['99999'],
            'pf-1-user': ['99999'],
            'ef-TOTAL_FORMS': ['2'],
            'pf-MIN_NUM_FORMS': ['0'],
            'pf-INITIAL_FORMS': ['1'],
            'ef-0-id': ['10'],
            'wf-1-url': [''],
            'preferred_photo': ['AUTO'],
            'ef-0-address': ['awilliam@tjhsst.edu'],
            'ef-INITIAL_FORMS': ['1'],
            'pf-0-purpose': ['h'],
            'ef-MAX_NUM_FORMS': ['1000'],
            'wf-1-id': [''],
            'wf-INITIAL_FORMS': ['1'],
            'ef-0-DELETE': ['on'],
            'pf-0-user': ['99999'],
            'ef-1-user': ['99999'],
            'show_pictures': ['on']
        }
        with self.assertLogs("intranet.apps.preferences.views", "DEBUG") as logger:
            response = self.client.post(reverse('preferences'), pref_dict)
        self.assertNotEqual(logger.output, [
            "DEBUG:intranet.apps.preferences.views:Unable to set field phones with value []"
            ": Can not set User attribute 'phones' -- not in user attribute list."
        ])
        self.assertEqual(response.status_code, 302)
