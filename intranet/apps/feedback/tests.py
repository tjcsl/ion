from django.urls import reverse

from ...test.ion_test import IonTestCase


class FeedbackTest(IonTestCase):
    def test_send_feedback_view(self):
        self.make_admin()

        response = self.client.get(reverse("send_feedback"))
        self.assertEqual(response.status_code, 200)

        with self.settings(PRODUCTION=False, FORCE_EMAIL_SEND=False):
            response = self.client.post(reverse("send_feedback"), {"comments": "This is a test of the feedback system."})
            self.assertEqual(response.status_code, 200)

    def test_send_feedback_unauthenticated(self):
        self.client.logout()

        response = self.client.get(reverse("send_feedback"))
        self.assertRedirects(response, "/login?next=/feedback", status_code=302)
