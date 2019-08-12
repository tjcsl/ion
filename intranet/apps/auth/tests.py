import datetime
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup


class GrantAdminTest(IonTestCase):
    """Tests granting admin to an user."""

    def test_grant_admin(self):
        """Tests giving an valid user admin_all."""
        out = StringIO()
        call_command("grant_admin", "awilliam", "admin_all", stdout=out)
        self.assertEqual(out.getvalue().strip(), "Added awilliam to admin_all")


class LoginViewTest(IonTestCase):
    """Tests of the login page (but not actually auth)"""

    def test_login_page(self):
        self.assertEqual(self.client.get(reverse("index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("about")).status_code, 200)
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def login_student(self):
        user = get_user_model().objects.get_or_create(username="awilliam")[0]
        user.user_type = "student"
        user.first_login = timezone.now()
        user.seen_welcome = True
        user.save()
        with self.settings(MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw="):
            return self.client.post(reverse("login"), data={"username": "awilliam", "password": "dankmemes"})

    def does_login_redirect_to(self, url):
        response = self.login_student()
        return response.status_code == 302 and response["Location"] == url

    @staticmethod
    def create_block_by_signup_datetime(signup_datetime, **kwargs):
        return EighthBlock.objects.create(date=signup_datetime.date(), signup_time=signup_datetime.time(), **kwargs)

    def test_authentication(self):
        self.assertTrue(self.does_login_redirect_to(reverse("index")))

    def test_eighth_login_redirect(self):
        now = timezone.localtime(timezone.now())

        self.login_student()
        user = get_user_model().objects.get(username="awilliam")

        # Don't let blocks created in other tests contaminate these results
        EighthBlock.objects.all().delete()

        deltas = {minutes: datetime.timedelta(minutes=minutes) for minutes in (-5, 5, 10, 15, 25)}

        activity = EighthActivity.objects.create(name="Test Activity 1")

        with self.settings(ENABLE_PRE_EIGHTH_REDIRECT=True):
            block_25 = self.create_block_by_signup_datetime(now + deltas[25], block_letter="A")
            self.assertTrue(self.does_login_redirect_to(reverse("index")))
            EighthSignup.objects.create(user=user, scheduled_activity=EighthScheduledActivity.objects.create(block=block_25, activity=activity))
            self.assertTrue(self.does_login_redirect_to(reverse("index")))

            block_15 = self.create_block_by_signup_datetime(now + deltas[15], block_letter="B")
            self.assertTrue(self.does_login_redirect_to(reverse("eighth_signup")))
            EighthSignup.objects.create(user=user, scheduled_activity=EighthScheduledActivity.objects.create(block=block_15, activity=activity))
            self.assertTrue(self.does_login_redirect_to(reverse("index")))

            block_10 = self.create_block_by_signup_datetime(now + deltas[10], block_letter="C")
            self.assertTrue(self.does_login_redirect_to(reverse("eighth_signup")))
            EighthSignup.objects.create(user=user, scheduled_activity=EighthScheduledActivity.objects.create(block=block_10, activity=activity))
            self.assertTrue(self.does_login_redirect_to(reverse("index")))

            block_5 = self.create_block_by_signup_datetime(now + deltas[5], block_letter="D")
            self.assertTrue(self.does_login_redirect_to(reverse("eighth_signup")))
            EighthSignup.objects.create(user=user, scheduled_activity=EighthScheduledActivity.objects.create(block=block_5, activity=activity))
            self.assertTrue(self.does_login_redirect_to(reverse("index")))

            block_n5 = self.create_block_by_signup_datetime(now + deltas[-5], block_letter="E")
            self.assertTrue(self.does_login_redirect_to(reverse("index")))
            EighthSignup.objects.create(user=user, scheduled_activity=EighthScheduledActivity.objects.create(block=block_n5, activity=activity))
            self.assertTrue(self.does_login_redirect_to(reverse("index")))

            EighthBlock.objects.all().delete()
