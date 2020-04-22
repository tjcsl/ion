from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from .models import CarApplication, ParkingApplication


class ParkingTest(IonTestCase):
    """Tests for the parking module."""

    def login_with_args(self, uname, grad_year):
        user = get_user_model().objects.get_or_create(username=uname, graduation_year=grad_year)[0]
        with self.settings(MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw="):
            self.client.login(username=uname, password="dankmemes")
        return user

    def test_parking_form_junior(self):
        user = self.login_with_args("awilliam", get_senior_graduation_year() + 1)

        response = self.client.post(reverse("parking_form"), data={"email": user.tj_email, "mentorship": False})

        self.assertEqual(response.status_code, 302)

        # Check that a parking application was created
        parking_apps = ParkingApplication.objects.filter(user=user)
        self.assertTrue(parking_apps.exists())
        self.assertEqual(parking_apps.count(), 1)

        response = self.client.post(reverse("parking_car"), data={"license_plate": "TJCSL", "make": "Lamborghini", "model": "Veneno", "year": 2018})

        self.assertEqual(response.status_code, 302)

        # Check that a parking application was created
        car_apps = CarApplication.objects.filter(user=user)
        self.assertTrue(car_apps.exists())
        self.assertEqual(car_apps.count(), 1)

        # Check for association with parking form
        parking_apps = ParkingApplication.objects.filter(user=user)
        self.assertTrue(parking_apps[0].cars.count(), 1)

    def test_invalid_user(self):
        user = self.login_with_args("bwilliam", get_senior_graduation_year() + 2)

        response = self.client.post(reverse("parking_form"), data={"email": user.tj_email, "mentorship": False})

        # Check that parking application was not created
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ParkingApplication.objects.filter(user=user).exists())

        response = self.client.post(reverse("parking_car"), data={"license_plate": "TJCSL", "make": "Lamborghini", "model": "Veneno", "year": "2018"})

        # Check that car application is not created
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ParkingApplication.objects.filter(user=user).exists())
