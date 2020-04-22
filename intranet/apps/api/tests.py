import datetime
import json
import urllib.parse

from oauth2_provider.models import AccessToken, get_application_model
from oauth2_provider.settings import oauth2_settings

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..bus.models import Route
from ..eighth.models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup
from ..schedule.models import Block, Day, DayType, Time

Application = get_application_model()


class ApiTest(IonTestCase):
    """Tests for the api module."""

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username="awilliam", graduation_year=(get_senior_graduation_year() + 1))[0]
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

        self.auth = None

    def make_token(self):
        tok = AccessToken.objects.create(
            user=self.user, token="1234567890", application=self.application, scope="read write", expires=timezone.now() + datetime.timedelta(days=1)
        )
        self.auth = "Bearer {}".format(tok.token)

    def get_api_eighth_block_list(self, query=""):
        return self.client.get(reverse("api_eighth_block_list") + query, HTTP_AUTHORIZATION=self.auth)

    def get_api_eighth_signup_list(self, query=""):
        return self.client.get(reverse("api_eighth_user_signup_list_myid") + query, HTTP_AUTHORIZATION=self.auth)

    def test_get_emerg(self):
        response = self.client.get(reverse("api_emerg_status"))
        self.assertEqual(response.status_code, 200)

    def test_get_profile(self):
        self.make_token()
        response = self.client.get(reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api_user_profile_detail", args=[9001]), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 404)

    def test_get_announcements(self):
        self.make_token()
        response = self.client.get(reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api_announcements_detail", args=[9001]), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 404)

    def test_oauth_read(self):

        self.make_token()
        response = self.client.get(reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth)
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
            user=self.user,
            token="1234567890",
            application=self.client_credentials_application,
            scope="read write",
            expires=timezone.now() + datetime.timedelta(days=1),
        )
        auth = "Bearer {}".format(tok.token)

        # List announcements
        response = self.client.get(reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=auth)
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
        response = self.client.get(reverse("api_eighth_block_detail", kwargs={"pk": block.pk}), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content.decode())
        self.assertTrue("id" in resp)

        # Should be able to list profile
        response = self.client.get(reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test_oauth_client_credentials_read_anonymous(self):
        tok = AccessToken.objects.create(
            user=None,
            token="1234567890",
            application=self.client_credentials_application,
            scope="read write",
            expires=timezone.now() + datetime.timedelta(days=1),
        )
        auth = "Bearer {}".format(tok.token)

        # List announcements
        response = self.client.get(reverse("api_announcements_list_create"), HTTP_AUTHORIZATION=auth)
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
        response = self.client.get(reverse("api_eighth_block_detail", kwargs={"pk": block.pk}), HTTP_AUTHORIZATION=auth)
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

    def test_api_schedule_detail(self):
        self.make_token()

        today = timezone.localdate()
        one_day = datetime.timedelta(days=1)

        Day.objects.filter(date__gte=today - one_day, date__lte=today + one_day).delete()
        no_school_type = DayType.objects.get_or_create(name="NO SCHOOL<br>", special=True)[0]
        Day.objects.create(date=today, day_type=no_school_type)

        test_day_type = DayType.objects.get_or_create(name="Test day")[0]
        test_day_type.blocks.add(
            Block.objects.create(
                name="Test period", start=Time.objects.create(hour=10, minute=0), end=Time.objects.create(hour=11, minute=0), order=1
            )
        )
        Day.objects.create(date=today - one_day, day_type=test_day_type)

        date_str = (today - one_day).strftime("%Y-%m-%d")
        url = reverse("api_schedule_day_detail", kwargs={"date": date_str})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(urllib.parse.urlparse(response.json()["url"]).path, url)
        self.assertEqual(response.json()["date"], date_str)
        self.assertEqual(response.json()["day_type"]["name"], test_day_type.name)
        self.assertEqual(response.json()["day_type"]["special"], False)
        self.assertEqual(response.json()["day_type"]["blocks"], [{"order": 1, "name": "Test period", "start": "10:00", "end": "11:00"}])

        for day in [today, today + one_day]:
            date_str = day.strftime("%Y-%m-%d")
            url = reverse("api_schedule_day_detail", kwargs={"date": date_str})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(urllib.parse.urlparse(response.json()["url"]).path, url)
            self.assertEqual(response.json()["date"], date_str)
            self.assertEqual(response.json()["day_type"]["name"], no_school_type.name)
            self.assertEqual(response.json()["day_type"]["special"], no_school_type.special)
            self.assertEqual(response.json()["day_type"]["blocks"], [])

    def test_api_eighth_block_list(self):
        self.make_token()

        # Don't let blocks created in other tests contaminate these results
        EighthBlock.objects.all().delete()

        # List everything
        response = self.get_api_eighth_block_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

        # Test a good date
        response = self.get_api_eighth_block_list("?date=2019-04-18")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

        # Test a bad date
        response = self.get_api_eighth_block_list("?date=2019-04-18bad")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ["Invalid format for date."])

        # Test a good start date
        response = self.get_api_eighth_block_list("?start_date=2019-04-18")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

        # Test a bad start date
        response = self.get_api_eighth_block_list("?start_date=2019-04-18bad")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ["Invalid format for start_date."])

        # Now let's add some data
        now = timezone.localtime(timezone.now())
        block_old = EighthBlock.objects.create(date=(now - datetime.timedelta(days=370)).date(), block_letter="A")
        block_new = EighthBlock.objects.create(date=now.date(), block_letter="A")
        block_old_date_str = block_old.date.strftime("%Y-%m-%d")
        block_new_date_str = block_new.date.strftime("%Y-%m-%d")
        future_date_str = (block_new.date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        # List everything
        response = self.get_api_eighth_block_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["id"], block_new.id)
        self.assertEqual(response.json()["results"][0]["date"], block_new_date_str)
        self.assertEqual(response.json()["results"][0]["block_letter"], block_new.block_letter)

        # Test a date with a block scheduled
        response = self.get_api_eighth_block_list("?date=" + block_new_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["id"], block_new.id)
        self.assertEqual(response.json()["results"][0]["date"], block_new_date_str)
        self.assertEqual(response.json()["results"][0]["block_letter"], block_new.block_letter)

        # Test another date with a block scheduled
        response = self.get_api_eighth_block_list("?date=" + block_old_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["id"], block_old.id)
        self.assertEqual(response.json()["results"][0]["date"], block_old_date_str)
        self.assertEqual(response.json()["results"][0]["block_letter"], block_old.block_letter)

        # Test a date with no blocks scheduled
        response = self.get_api_eighth_block_list("?date=" + future_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

        # Test a start date with blocks scheduled
        response = self.get_api_eighth_block_list("?start_date=" + block_new_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["id"], block_new.id)
        self.assertEqual(response.json()["results"][0]["date"], block_new_date_str)
        self.assertEqual(response.json()["results"][0]["block_letter"], block_new.block_letter)

        # Test an earlier start date
        response = self.get_api_eighth_block_list("?start_date=" + block_old_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 2)
        self.assertEqual(response.json()["results"][0]["id"], block_old.id)
        self.assertEqual(response.json()["results"][0]["date"], block_old_date_str)
        self.assertEqual(response.json()["results"][0]["block_letter"], block_old.block_letter)
        self.assertEqual(response.json()["results"][1]["id"], block_new.id)
        self.assertEqual(response.json()["results"][1]["date"], block_new_date_str)
        self.assertEqual(response.json()["results"][1]["block_letter"], block_new.block_letter)

        # Test a late start date
        response = self.get_api_eighth_block_list("?start_date=" + future_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

        # Test that past blocks are shown if there are no upcoming blocks
        EighthBlock.objects.all().delete()
        block = EighthBlock.objects.create(date=(now - datetime.timedelta(days=1)).date(), block_letter="A")
        block_date_str = block.date.strftime("%Y-%m-%d")
        response = self.get_api_eighth_block_list("?date=" + block_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["id"], block.id)
        self.assertEqual(response.json()["results"][0]["date"], block_date_str)
        self.assertEqual(response.json()["results"][0]["block_letter"], block.block_letter)

    def test_api_eighth_signup_list(self):
        self.make_token()

        # Don't let blocks created in other tests contaminate these results
        EighthBlock.objects.all().delete()

        act1 = EighthActivity.objects.create(name="Test Activity 1")
        act2 = EighthActivity.objects.create(name="Test Activity 2")

        # Check the list
        response = self.get_api_eighth_signup_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Test a good date
        response = self.get_api_eighth_signup_list("?date=2019-04-18")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Test a bad date
        response = self.get_api_eighth_signup_list("?date=2019-04-18bad")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ["Invalid format for date."])

        # Test a good start date
        response = self.get_api_eighth_signup_list("?start_date=2019-04-18")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Test a bad start date
        response = self.get_api_eighth_signup_list("?start_date=2019-04-18bad")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ["Invalid format for start_date."])

        # Create some blocks
        now = timezone.localtime(timezone.now())
        block1 = EighthBlock.objects.create(date=(now - datetime.timedelta(days=370)).date(), block_letter="A")
        schact1 = EighthScheduledActivity.objects.create(block=block1, activity=act1)
        block2 = EighthBlock.objects.create(date=now.date(), block_letter="A")
        schact2 = EighthScheduledActivity.objects.create(block=block2, activity=act2)

        block1_date_str = block1.date.strftime("%Y-%m-%d")
        block2_date_str = block2.date.strftime("%Y-%m-%d")
        future_date_str = (block2.date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        # Check the list
        response = self.get_api_eighth_signup_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Sign up
        sgn1 = EighthSignup.objects.create(user=self.user, scheduled_activity=schact1)

        # Check the list
        response = self.get_api_eighth_signup_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Test a start date with an upcoming signup
        response = self.get_api_eighth_signup_list("?start_date=" + block1_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], sgn1.id)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact1.id)
        self.assertEqual(response.json()[0]["block"]["id"], block1.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act1.id)

        # Test a date with an upcoming signup
        response = self.get_api_eighth_signup_list("?date=" + block1_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], sgn1.id)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact1.id)
        self.assertEqual(response.json()[0]["block"]["id"], block1.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act1.id)

        # Test a start date with no upcoming signups
        response = self.get_api_eighth_signup_list("?start_date=" + future_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Test a date with no signups
        response = self.get_api_eighth_signup_list("?date=" + future_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Sign up for another block
        sgn2 = EighthSignup.objects.create(user=self.user, scheduled_activity=schact2)

        # Check the list
        response = self.get_api_eighth_signup_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], sgn2.id)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact2.id)
        self.assertEqual(response.json()[0]["block"]["id"], block2.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act2.id)

        # Test a date with a signup
        response = self.get_api_eighth_signup_list("?date=" + block1_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], sgn1.id)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact1.id)
        self.assertEqual(response.json()[0]["block"]["id"], block1.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act1.id)

        # Test another date with a signup
        response = self.get_api_eighth_signup_list("?date=" + block2_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], sgn2.id)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact2.id)
        self.assertEqual(response.json()[0]["block"]["id"], block2.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act2.id)

        # Test a start date with two upcoming signups
        response = self.get_api_eighth_signup_list("?start_date=" + block1_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["id"], sgn1.id)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact1.id)
        self.assertEqual(response.json()[0]["block"]["id"], block1.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act1.id)
        self.assertEqual(response.json()[1]["id"], sgn2.id)
        self.assertEqual(response.json()[1]["user"], self.user.id)
        self.assertEqual(response.json()[1]["scheduled_activity"], schact2.id)
        self.assertEqual(response.json()[1]["block"]["id"], block2.id)
        self.assertEqual(response.json()[1]["activity"]["id"], act2.id)

        # Test a start date with an upcoming signup
        response = self.get_api_eighth_signup_list("?start_date=" + block2_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["user"], self.user.id)
        self.assertEqual(response.json()[0]["scheduled_activity"], schact2.id)
        self.assertEqual(response.json()[0]["block"]["id"], block2.id)
        self.assertEqual(response.json()[0]["activity"]["id"], act2.id)

        # Test a start date with no upcoming signups
        response = self.get_api_eighth_signup_list("?start_date=" + future_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Test a date with no signups
        response = self.get_api_eighth_signup_list("?date=" + future_date_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_api_bus_list(self):
        self.make_token()
        route = Route.objects.create(route_name="JT-001", bus_number="JT-001")
        response = self.client.get(reverse("api_bus_list"), HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results, [{"id": route.id, "status": "o", "route_name": route.route_name, "bus_number": route.bus_number, "space": ""}])

    def test_api_bus_detail(self):
        self.make_token()
        route_1 = Route.objects.create(route_name="JT-001", bus_number="JT-001")
        response = self.client.get(reverse("api_bus_detail", args=[route_1.pk]), HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"id": route_1.id, "route_name": route_1.route_name, "space": "", "bus_number": route_1.bus_number, "status": "o"}
        )
