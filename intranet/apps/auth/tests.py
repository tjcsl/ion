import datetime
from io import StringIO

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from .forms import AuthenticateForm
from .widgets import TurnstileField, TurnstileWidget


class TurnstileFieldTest(IonTestCase):
    """Unit tests for the TurnstileField widget."""

    def test_turnstile_disabled(self):
        """Test that Turnstile bypasses validation when disabled."""
        field = TurnstileField(required=False)
        with self.settings(TURNSTILE_ENABLED=False):
            # Should accept any value (or None) when disabled
            self.assertIsNone(field.clean(None))
            self.assertEqual(field.clean("fake-token"), "fake-token")

    def test_turnstile_required_field(self):
        """Test that required Turnstile field rejects None."""
        field = TurnstileField(required=True)
        with self.settings(TURNSTILE_ENABLED=True, TESTING=True, TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA"):
            with self.assertRaises(ValidationError):
                field.clean(None)

    def test_turnstile_pass_key_in_testing(self):
        """Test that CF turnstile success keys in testing mode pass."""
        field = TurnstileField(required=True)
        with self.settings(
            TURNSTILE_ENABLED=True,
            TESTING=True,
            TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",
            TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        ):
            # no network i/o during testing is preferred
            result = field.clean("dummy-token")
            self.assertEqual(result, "dummy-token")

    def test_turnstile_pass_key_invisible_variant(self):
        """Test that 1x...BB (invisible pass) keys work."""
        field = TurnstileField(required=True)
        with self.settings(
            TURNSTILE_ENABLED=True,
            TESTING=True,
            TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000BB",
            TURNSTILE_SITE_KEY="1x00000000000000000000BB",
        ):
            result = field.clean("dummy-token")
            self.assertEqual(result, "dummy-token")

    def test_turnstile_fail_key_in_testing(self):
        """Test that CF turnstile failure keys in testing mode fail."""
        field = TurnstileField(required=True)
        with self.settings(
            TURNSTILE_ENABLED=True,
            TESTING=True,
            TURNSTILE_SECRET_KEY="2x0000000000000000000000000000000AA",
            TURNSTILE_SITE_KEY="2x00000000000000000000AA",
        ):
            # should fail w/o making network request
            with self.assertRaises(ValidationError) as cm:
                field.clean("dummy-token")  # the value doesn't matter in testing/ci
            self.assertIn("Invalid turnstile response", str(cm.exception))

    def test_turnstile_invalid_key_in_testing(self):
        """Test that non-test keys fail in TESTING mode."""
        field = TurnstileField(required=True)
        with self.settings(
            TURNSTILE_ENABLED=True, TESTING=True, TURNSTILE_SECRET_KEY="invalid-production-key", TURNSTILE_SITE_KEY="invalid-site-key"
        ):
            # Should *theoretically* fail since it's not a valid test key
            with self.assertRaises(ValidationError) as cm:
                field.clean("dummy-token")
            self.assertIn("Invalid turnstile response", str(cm.exception))

    def test_turnstile_in_ci_mode(self):
        """Test that Turnstile works in IN_CI mode."""
        field = TurnstileField(required=True)
        with self.settings(
            TURNSTILE_ENABLED=True,
            IN_CI=True,
            TESTING=False,
            TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",
            TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        ):
            # passes in CI with test keys
            result = field.clean("dummy-token")
            self.assertEqual(result, "dummy-token")  # pass!


class AuthenticateFormTest(IonTestCase):
    """Tests dynamic Turnstile form configuration."""

    def test_turnstile_disabled_in_form(self):
        with self.settings(TURNSTILE_ENABLED=False):
            field = AuthenticateForm().fields["turnstile"]
            self.assertFalse(field.required)
            self.assertIsInstance(field.widget, forms.HiddenInput)

    def test_turnstile_enabled_in_form(self):
        with self.settings(TURNSTILE_ENABLED=True):
            field = AuthenticateForm().fields["turnstile"]
            self.assertTrue(field.required)
            self.assertIsInstance(field.widget, TurnstileWidget)


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
        with self.settings(
            MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw=",
            TURNSTILE_ENABLED=False,
            TESTING=True,
        ):
            return self.client.post(reverse("login"), data={"username": "awilliam", "password": "dankmemes"})

    def login_with_turnstile(self, should_pass=True):
        """Helper to test login with Turnstile enabled."""
        user = get_user_model().objects.get_or_create(username="awilliam")[0]
        user.user_type = "student"
        user.first_login = timezone.now()
        user.seen_welcome = True
        user.save()

        # use 1x for pass, 2x for fail
        secret_key = "1x0000000000000000000000000000000AA" if should_pass else "2x0000000000000000000000000000000AA"
        site_key = "1x00000000000000000000AA" if should_pass else "2x00000000000000000000AB"

        with self.settings(
            MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw=",
            TURNSTILE_ENABLED=True,
            TURNSTILE_SECRET_KEY=secret_key,
            TURNSTILE_SITE_KEY=site_key,
            TESTING=True,
        ):
            return self.client.post(reverse("login"), data={"username": "awilliam", "password": "dankmemes", "cf-turnstile-response": "dummy-token"})

    def does_login_redirect_to(self, url):
        response = self.login_student()
        return response.status_code == 302 and response["Location"] == url

    @staticmethod
    def create_block_by_signup_datetime(signup_datetime, **kwargs):
        return EighthBlock.objects.create(date=signup_datetime.date(), signup_time=signup_datetime.time(), **kwargs)

    def test_authentication(self):
        self.assertTrue(self.does_login_redirect_to(reverse("index")))

    def test_login_with_turnstile_pass(self):
        """Test that login succeeds with valid Turnstile token (1x key)."""
        response = self.login_with_turnstile(should_pass=True)
        # Should redirect to index on success
        self.assertEqual(302, response.status_code)
        self.assertEqual(response["Location"], reverse("index"))

    def test_login_with_turnstile_fail(self):
        """Test that login fails with invalid Turnstile token (2x key)."""
        response = self.login_with_turnstile(should_pass=False)
        # Should stay on login page (200) and show error
        self.assertEqual(200, response.status_code)
        # Check that we're still on the login page
        self.assertContains(response, "login", status_code=200)

    def test_login(self):
        """Just test PAM login, but not really because PAM isn't accessible from here..."""

        response = self.client.post(reverse("login"), data={"username": "awilliam", "password": "dankmemes123"})
        self.assertEqual(200, response.status_code)

    def test_logout_view(self):
        self.login()
        response = self.client.get(reverse("logout"))
        self.assertEqual(302, response.status_code)

    def test_reauthentication_view(self):
        self.login()
        response = self.client.get(reverse("reauth"))
        self.assertEqual(200, response.status_code)

        with self.settings(
            MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw=",
        ):
            response = self.client.post(reverse("reauth"), data={"password": "dankmemes"})
            self.assertEqual(302, response.status_code)

    def test_reset_password_view(self):
        self.login()
        response = self.client.get(reverse("reset_password"))
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse("reset_password"),
            data={
                "username": "awilliam",
                "old_password": "dankmemes",
                "new_password": "dankmemes",
                "new_password_confirm": "dankmemes",
            },
        )
        self.assertEqual(200, response.status_code)

    def test_eighth_login_redirect(self):
        now = timezone.localtime(timezone.now())

        self.login_student()
        user = get_user_model().objects.get(username="awilliam")

        # Don't let blocks created in other tests contaminate these results
        EighthBlock.objects.all().delete()

        deltas = {minutes: datetime.timedelta(minutes=minutes) for minutes in (-5, 5, 10, 15, 25)}

        activity = EighthActivity.objects.create(name="Test Activity 1")

        with self.settings(ENABLE_PRE_EIGHTH_CLOSE_SIGNUP_REDIRECT=True):
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
