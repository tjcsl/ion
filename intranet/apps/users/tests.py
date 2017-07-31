# -*- coding: utf-8 -*-

from io import StringIO

from django.core.management import call_command
from django.urls import reverse

from ...test.ion_test import IonTestCase


class DynamicGroupTest(IonTestCase):
    """Tests creating dynamic groups."""

    def test_dynamic_groups(self):
        out = StringIO()
        with self.settings(SENIOR_GRADUATION_YEAR=2016):
            call_command('dynamic_groups', stdout=out)
        output = [
            "2016: 0 users", "2016: Processed", "2017: 1 users", "2017: Processed", "2018: 0 users", "2018: Processed", "2019: 0 users",
            "2019: Processed", "Done."
        ]
        self.assertEqual(out.getvalue().splitlines(), output)


class ProfileTest(IonTestCase):

    def test_get_profile(self):
        self.make_admin()
        # Check for non-existant user.
        response = self.client.get(reverse('api_user_profile_detail', args=[42]))
        self.assertEqual(response.status_code, 404)
        # Get data for ourself.
        response = self.client.get(reverse('api_user_myprofile_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['address']['postal_code'], '22182')
