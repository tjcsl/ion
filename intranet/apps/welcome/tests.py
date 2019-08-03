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
