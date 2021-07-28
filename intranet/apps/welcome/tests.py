from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase


class WelcomeTest(IonTestCase):
    """Tests for the welcome module."""

    def test_welcome_view_teacher(self):
        user = self.login()
        user.user_type = "teacher"
        user.save()
        response = self.client.get(reverse("welcome"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["first_login"], False)
        self.assertTemplateUsed(response, "welcome/teacher.html")

    def test_welcome_view_student(self):
        _ = self.login()
        response = self.client.get(reverse("welcome"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "welcome/student.html")

    def test_welcome_done(self):
        user = self.login()
        self.assertFalse(user.seen_welcome)
        response = self.client.get(reverse("welcome_done"))
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(get_user_model().objects.get(seen_welcome=True), user)

    def test_oauth_welcome(self):
        # When a user logs in and is expected to be redirected to an oauth application, they shouldn't see the welcome
        user = self.login()
        user.seen_welcome = False
        user.save()
        self.client.get(reverse("oauth_redirect"))
        self.assertFalse(user.seen_welcome)
