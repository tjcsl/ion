from django.urls import reverse

from ...test.ion_test import IonTestCase


class FeedbackTest(IonTestCase):
    def test_send_feedback_view(self):
        self.make_admin()

        response = self.client.get(reverse("send_feedback"))
        self.assertEqual(response.status_code, 200)
