# -*- coding: utf-8 -*-

from io import StringIO

from django.core.management import call_command
from django.urls import reverse

from .models import UserCache

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


class CacheTest(IonTestCase):
    def test_clear_cache(self):
        user = self.make_admin()
        # clear as if using shell
        user.clear_cache()
        # clear cache as if using web interface
        response = self.client.get(reverse('user_profile'), {"clear_cache": 1})
        self.assertEqual(response.status_code, 302)

    def test_view_profile(self):
        self.login()
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)

    def test_property_without_cache(self):
        user = self.make_admin()
        # delete cache object related to user
        UserCache.objects.filter(user=user).delete()
        # make sure correct exception is raised when accessing a nonexistent object
        with self.assertRaises(UserCache.DoesNotExist):
            self.assertIsNotNone(user.cache.gender)
        # make sure user.cache does not exist
        with self.assertRaises(UserCache.DoesNotExist):
            self.assertIsNotNone(user.cache)
        # gender is not accessible, so returns None and sets cache
        self.assertIsNone(user.get_or_set_cache('gender'))
        # make sure cache was set by get_or_set_cache
        self.assertIsNotNone(user.cache)
        # delete cache object related to user
        UserCache.objects.filter(user=user).delete()
        # make sure user.is_male is false and does not fail, i.e checks LDAP and sets cache
        self.assertFalse(user.is_male)
        # make sure cache was set
        self.assertIsNotNone(user.cache)
        # delete cache object related to user
        UserCache.objects.filter(user=user).delete()
        # make sure getting the profile with no cache works
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)
