import datetime

from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from .models import FeatureAnnouncement


class FeaturesTest(IonTestCase):
    def test_anonymous_feature_list(self):
        """Tests listing features on the login page as an anonymous user."""
        self.client.logout()

        FeatureAnnouncement.objects.all().delete()

        for view_name in ["index", "login"]:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)
            self.assertQuerysetEqual(response.context["feature_announcements"], [])

        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)
        far_past = today - datetime.timedelta(days=7)
        tomorrow = today + datetime.timedelta(days=1)
        far_future = today + datetime.timedelta(days=7)

        FeatureAnnouncement.objects.create(activation_date=far_past, expiration_date=yesterday, context="login", announcement_html="Test 1")
        fa2 = FeatureAnnouncement.objects.create(activation_date=yesterday, expiration_date=today, context="login", announcement_html="Test 2")
        fa3 = FeatureAnnouncement.objects.create(activation_date=today, expiration_date=today, context="login", announcement_html="Test 3")
        fa4 = FeatureAnnouncement.objects.create(activation_date=today, expiration_date=tomorrow, context="login", announcement_html="Test 4")
        FeatureAnnouncement.objects.create(activation_date=tomorrow, expiration_date=far_future, context="login", announcement_html="Test 5")

        for view_name in ["index", "login"]:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)
            self.assertQuerysetEqual(response.context["feature_announcements"], list(map(repr, [fa2, fa3, fa4])), ordered=False)

    def test_login_feature_list(self):
        """Tests listing features on the login/dashboard/eighth signup pages as an authenticated user."""
        user = self.login()

        FeatureAnnouncement.objects.all().delete()

        for view_name in ["index", "login", "eighth_signup"]:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)
            self.assertQuerysetEqual(response.context["feature_announcements"], [])

        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)
        far_past = today - datetime.timedelta(days=7)
        tomorrow = today + datetime.timedelta(days=1)
        far_future = today + datetime.timedelta(days=7)

        FeatureAnnouncement.objects.create(activation_date=far_past, expiration_date=yesterday, context="eighth_signup", announcement_html="Test 1")
        fa2 = FeatureAnnouncement.objects.create(activation_date=yesterday, expiration_date=today, context="dashboard", announcement_html="Test 2")
        fa3 = FeatureAnnouncement.objects.create(activation_date=today, expiration_date=today, context="eighth_signup", announcement_html="Test 3")
        fa4 = FeatureAnnouncement.objects.create(activation_date=today, expiration_date=tomorrow, context="login", announcement_html="Test 4")
        FeatureAnnouncement.objects.create(activation_date=tomorrow, expiration_date=far_future, context="dashboard", announcement_html="Test 5")

        for view_name, announcement in [("index", fa2), ("login", fa4), ("eighth_signup", fa3)]:
            self.assertFalse(announcement.users_seen.filter(id=user.id).exists())
            self.assertFalse(announcement.users_dismissed.filter(id=user.id).exists())

            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)
            self.assertQuerysetEqual(response.context["feature_announcements"], [repr(announcement)], ordered=False)

            self.assertTrue(announcement.users_seen.filter(id=user.id).exists())

            self.client.post(reverse("features:dismiss_feat_announcement", args=(announcement.id,)))

            self.assertTrue(announcement.users_dismissed.filter(id=user.id).exists())

            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)
            self.assertQuerysetEqual(response.context["feature_announcements"], [], ordered=False)
