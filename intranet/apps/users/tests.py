from io import StringIO
import datetime

from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import get_application_model, AccessToken
from oauth2_provider.settings import oauth2_settings

from .models import User, Address
from ...test.ion_test import IonTestCase

Application = get_application_model()


class DynamicGroupTest(IonTestCase):
    """Tests creating dynamic groups."""

    def test_dynamic_groups(self):
        out = StringIO()
        with self.settings(SENIOR_GRADUATION_YEAR=2016):
            User.objects.get_or_create(
                username="awilliam", graduation_year=settings.SENIOR_GRADUATION_YEAR + 1
            )
            call_command("dynamic_groups", stdout=out)
        output = [
            "2016: 0 users",
            "2016: Processed",
            "2017: 1 users",
            "2017: Processed",
            "2018: 0 users",
            "2018: Processed",
            "2019: 0 users",
            "2019: Processed",
            "Done.",
        ]
        self.assertEqual(out.getvalue().splitlines(), output)


class ProfileTest(IonTestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username="awilliam")[0]
        address = Address.objects.get_or_create(
            street="6560 Braddock Rd", city="Alexandria", state="VA", postal_code="22312"
        )[0]
        self.user.properties._address = address # pylint: disable=protected-access
        self.user.properties.save()
        self.user.save()
        self.application = Application(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        self.application.save()

        self.client_credentials_application = Application(
            name="Test Client Credentials Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        self.client_credentials_application.save()

        oauth2_settings._SCOPES = ["read", "write"] # pylint: disable=protected-access

    def make_token(self):
        tok = AccessToken.objects.create(
            user=self.user,
            token="1234567890",
            application=self.application,
            scope="read write",
            expires=timezone.now() + datetime.timedelta(days=1),
        )
        self.auth = "Bearer {}".format(tok.token)

    def test_get_profile(self):
        self.make_admin()
        self.make_token()
        # Check for non-existant user.
        response = self.client.get(
            reverse("api_user_profile_detail", args=[42]), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 404)
        # Get data for ourself.
        response = self.client.get(
            reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["address"]["postal_code"], "22312")
