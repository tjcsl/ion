# -*- coding: utf-8 -*-

from django.urls import reverse

from ...test.ion_test import IonTestCase


class ApiTest(IonTestCase):
    """Tests for the api module."""

    def test_get_profile(self):
        self.login()
        response = self.client.get(reverse('api_user_myprofile_detail'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('api_user_profile_detail', args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_get_announcements(self):
        self.login()
        response = self.client.get(reverse('api_announcements_list_create'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('api_announcements_detail', args=[9001]))
        self.assertEqual(response.status_code, 404)
