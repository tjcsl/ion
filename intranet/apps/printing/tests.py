from django.urls import reverse

from ...test.ion_test import IonTestCase


class PrintingTest(IonTestCase):
    def test_printing_view(self):
        self.make_admin()

        response = self.client.get(reverse("printing"))
        self.assertEqual(response.status_code, 200)
