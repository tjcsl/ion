import json
import datetime

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from oauth2_provider.models import get_application_model, AccessToken
from oauth2_provider.settings import oauth2_settings

from ..bus.models import Route
from ..eighth.models import EighthBlock, EighthActivity, EighthScheduledActivity, EighthRoom
from ...test.ion_test import IonTestCase

Application = get_application_model()


class ApiTest(IonTestCase):
    """Tests for the api module."""

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(
            username="awilliam", graduation_year=(settings.SENIOR_GRADUATION_YEAR + 1)
        )[0]
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

        oauth2_settings._SCOPES = ["read", "write"]  # pylint: disable=protected-access

    def make_token(self):
        tok = AccessToken.objects.create(
            user=self.user,
            token="1234567890",
            application=self.application,
            scope="read write",
            expires=timezone.now() + datetime.timedelta(days=1),
        )
        self.auth = "Bearer {}".format(tok.token)

    def test_get_emerg(self):
        response = self.client.get(reverse("api_emerg_status"))
        self.assertEqual(response.status_code, 200)

    def test_get_profile(self):
        self.make_token()
        response = self.client.get(
            reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("api_user_profile_detail", args=[9001]), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 404)

    def test_get_announcements(self):
        self.make_token()
        response = self.client.get(
            reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("api_announcements_detail", args=[9001]), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 404)

    def test_oauth_read(self):

        self.make_token()
        response = self.client.get(
            reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.status_code, 200)
        parsed_response = json.loads(response.content.decode())
        self.assertEqual(parsed_response["id"], int(self.user.id))
        self.assertEqual(parsed_response["ion_username"], self.user.username)

    def test_oauth_write(self):
        self.make_admin()

        self.make_token()

        block = EighthBlock.objects.create(date=datetime.datetime(2015, 1, 1), block_letter="A")
        room = EighthRoom.objects.create(name="room1", capacity=1)

        act = EighthActivity.objects.create(name="Test Activity 1")
        act.rooms.add(room)
        schact1 = EighthScheduledActivity.objects.create(activity=act, block=block)

        response = self.client.post(
            reverse("api_eighth_user_signup_list_myid"),
            {"scheduled_activity": schact1.id, "use_scheduled_activity": True},
            HTTP_AUTHORIZATION=self.auth,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(schact1.members.count(), 1)

    def test_oauth_client_credentials_read(self):
        tok = AccessToken.objects.create(
            user=None,
            token="1234567890",
            application=self.client_credentials_application,
            scope="read write",
            expires=timezone.now() + datetime.timedelta(days=1),
        )
        auth = "Bearer {}".format(tok.token)

        # List announcements
        response = self.client.get(
            reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=auth
        )
        self.assertEqual(response.status_code, 200)

        # List emergency status
        response = self.client.get(reverse("api_emerg_status"), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List schedule
        response = self.client.get(reverse("api_schedule_day_list"), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List activities
        response = self.client.get(reverse("api_eighth_activity_list"), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List blocks
        response = self.client.get(reverse("api_eighth_block_list"), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List specific block
        block = EighthBlock.objects.create(date=datetime.datetime(2015, 1, 1), block_letter="A")
        response = self.client.get(
            reverse("api_eighth_block_detail", kwargs={"pk": block.pk}), HTTP_AUTHORIZATION=auth
        )
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content.decode())
        self.assertTrue("id" in resp)

        # Should not be able to list profile
        response = self.client.get(reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 403)

    def test_no_credentials_read(self):
        # Announcements should only be available to logged in users
        response = self.client.get(reverse("api_announcements_list_create"))
        self.assertEqual(response.status_code, 401)

        # Activity list should only be available to logged in users
        response = self.client.get(reverse("api_eighth_activity_list"))
        self.assertEqual(response.status_code, 401)

        # Block list should only be available to logged in users
        response = self.client.get(reverse("api_eighth_block_list"))
        self.assertEqual(response.status_code, 401)

    def test_api_root(self):
        # Should be able to read API root without authentication
        response = self.client.get(reverse("api_root"))
        self.assertEqual(response.status_code, 200)

    def test_api_eighth_block_list(self):
        self.make_token()

        response = self.client.get(reverse("api_eighth_block_list"), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 200)

        # Test a good date
        response = self.client.get(
            reverse("api_eighth_block_list") + "?start_date=2019-04-18",
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, 200)

        # Test a bad date
        response = self.client.get(
            reverse("api_eighth_block_list") + "?start_date=2019-04-18bad",
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(response.status_code, 400)

    def test_api_bus_list(self):
        self.make_token()
        route = Route.objects.create(route_name="JT-001", bus_number="JT-001")
        response = self.client.get(reverse("api_bus_list"), HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results, [{'status': 'o', 'route_name': route.route_name, 'bus_number': route.bus_number, 'space': ''}])

    def test_api_bus_detail(self):
        self.make_token()
        route_1 = Route.objects.create(route_name="JT-001", bus_number="JT-001")
        response = self.client.get(reverse("api_bus_detail", args=[route_1.pk]), HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"route_name": route_1.route_name, "space": "", "bus_number": route_1.bus_number, "status": "o"})
