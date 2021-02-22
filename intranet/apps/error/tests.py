from django.test import Client
from django.urls import reverse

from ...test.ion_test import IonTestCase


class ErrorPageTest(IonTestCase):
    """Tests that the error pages (currently just 404 errors) render properly."""

    def test_404_page(self):
        resp = self.client.get("/nonexistent")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"The page you requested could not be found.", resp.content)
        self.login()
        resp = self.client.get("/nonexistent")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"The page you requested could not be found.", resp.content)

    def test_503_page(self):
        with self.settings(MAINTENANCE_MODE=True):
            resp = self.client.get(reverse("login"))
            self.assertEqual(resp.status_code, 503)
            self.assertIn(b"This site is currently undergoing maintenance", resp.content)

    def test_csrf_page(self):
        csrf_client = Client(enforce_csrf_checks=True)

        resp = csrf_client.post(reverse("login"), data={"sdlfkjsf": "sdlfjsdlfsd"})
        self.assertEqual(resp.status_code, 403)
        self.assertIn(b"If making a scripted request", resp.content)
