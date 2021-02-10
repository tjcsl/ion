from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from .models import SeniorEmailForward


class EmailFwdTest(IonTestCase):
    def test_email_fwd(self):
        """Email Forward sanity check."""
        user = get_user_model().objects.get_or_create(username="awilliam", graduation_year=get_senior_graduation_year() - 1, user_type="student")[0]
        self.login()

        response = self.client.get(reverse("senior_emailfwd"), follow=True)
        self.assertIn("Only seniors can set their forwarding address.", list(map(str, list(response.context["messages"]))))

        user.graduation_year = get_senior_graduation_year()
        user.save()

        response = self.client.get(reverse("senior_emailfwd"))
        self.assertEqual(response.status_code, 200)

        # Now, test setting an email
        response = self.client.post(reverse("senior_emailfwd"), data={"email": "nonexistent@tjhsst.edu"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, SeniorEmailForward.objects.filter(user=user, email="nonexistent@tjhsst.edu").count())

        # Test invalid email
        response = self.client.post(reverse("senior_emailfwd"), data={"email": "nonexistenttjhsst.edu"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, SeniorEmailForward.objects.filter(user=user, email="nonexistent@tjhsst.edu").count())
        self.assertIn("Error adding forwarding address.", list(map(str, list(response.context["messages"]))))
