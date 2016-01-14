# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from ...test.ion_test import IonTestCase


"""
Tests for the eighth module.
"""


class ApiTest(IonTestCase):

    def test_get_profile(self):
        self.login()
        response = self.client.get(reverse('api_user_myprofile_detail'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('api_user_profile_detail', args=[9001]))
        self.assertEqual(response.status_code, 404)
