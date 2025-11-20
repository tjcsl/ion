from django.urls import reverse

from ...test.ion_test import IonTestCase


class SessionMgmtTestCase(IonTestCase):
    def test_index_view(self):
        self.login()
        response = self.client.get(reverse("sessionmgmt"))
        self.assertEqual(200, response.status_code)

    def test_global_logout_view(self):
        self.login()
        response = self.client.post(reverse("global_logout"), data={"global_logout": "GLOBAL_LOGOUT"}, follow=True)
        self.assertEqual(200, response.status_code)

        # A test to see if we're on the login page
        self.assertIn("Login", str(response.content))
        self.assertIn("js/login.js", str(response.content))
