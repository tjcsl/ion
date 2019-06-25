

from django.conf import settings
from django.urls import reverse

from ..users.models import User
from ...test.ion_test import IonTestCase


class EmailFwdTest(IonTestCase):

    def test_email_fwd(self):
        """Email Forward sanity check."""
        User.objects.get_or_create(username="awilliam", graduation_year=settings.SENIOR_GRADUATION_YEAR)
        self.login()

        response = self.client.get(reverse('senior_emailfwd'))
        self.assertEqual(response.status_code, 200)
