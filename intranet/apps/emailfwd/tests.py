from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year


class EmailFwdTest(IonTestCase):
    def test_email_fwd(self):
        """Email Forward sanity check."""
        get_user_model().objects.get_or_create(username="awilliam", graduation_year=get_senior_graduation_year())
        self.login()

        response = self.client.get(reverse("senior_emailfwd"))
        self.assertEqual(response.status_code, 200)
