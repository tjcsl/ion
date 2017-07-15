# -*- coding: utf-8 -*-

import json
import datetime

from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import get_application_model, AccessToken
from oauth2_provider.settings import oauth2_settings

from ..users.models import User
from ..eighth.models import EighthBlock, EighthActivity, EighthScheduledActivity, EighthRoom
from ...test.ion_test import IonTestCase

Application = get_application_model()


class ApiTest(IonTestCase):
    """Tests for the api module."""

    def setUp(self):
        self.user = User.get_user(username="awilliam")
        self.application = Application(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE
        )
        self.application.save()

        self.client_credentials_application = Application(
            name="Test Client Credentials Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        self.client_credentials_application.save()

        oauth2_settings._SCOPES = ['read', 'write']

    def test_get_emerg(self):
        response = self.client.get(reverse('api_emerg_status'))
        self.assertEqual(response.status_code, 200)

    def test_get_profile(self):
        self.login()
        response = self.client.get(reverse('api_user_myprofile_detail'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('api_user_profile_detail', args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_get_announcements(self):
        self.login()
        response = self.client.get(reverse('api_announcements_list_create'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('api_announcements_detail', args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_oauth_read(self):
        tok = AccessToken.objects.create(
            user=self.user, token='1234567890',
            application=self.application, scope='read write',
            expires=timezone.now() + datetime.timedelta(days=1)
        )
        auth = "Bearer {}".format(tok.token)
        response = self.client.get(reverse('api_announcements_list_create'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('api_user_myprofile_detail'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        parsed_response = json.loads(response.content.decode())
        self.assertEqual(parsed_response["id"], int(self.user.id))
        self.assertEqual(parsed_response["ion_username"], self.user.username)

    def test_oauth_write(self):
        self.make_admin()

        tok = AccessToken.objects.create(
            user=self.user, token='1234567890',
            application=self.application, scope='read write',
            expires=timezone.now() + datetime.timedelta(days=1)
        )

        block = EighthBlock.objects.create(date=datetime.datetime(2015, 1, 1), block_letter='A')
        room = EighthRoom.objects.create(name="room1", capacity=1)

        act = EighthActivity.objects.create(name='Test Activity 1')
        act.rooms.add(room)
        schact1 = EighthScheduledActivity.objects.create(activity=act, block=block)

        auth = "Bearer {}".format(tok.token)
        response = self.client.post(reverse('api_eighth_user_signup_list_myid'), {
            "scheduled_activity": schact1.id,
            "use_scheduled_activity": True
        }, HTTP_AUTHORIZATION=auth)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(schact1.members.count(), 1)

    def test_oauth_client_credentials_read(self):
        tok = AccessToken.objects.create(
            user=None,
            token='1234567890',
            application=self.client_credentials_application,
            scope='read write',
            expires=timezone.now() + datetime.timedelta(days=1)
        )
        auth = "Bearer {}".format(tok.token)

        # List announcements
        response = self.client.get(reverse('api_announcements_list_create'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List emergency status
        response = self.client.get(reverse('api_emerg_status'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List schedule
        response = self.client.get(reverse('api_schedule_day_list'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List activities
        response = self.client.get(reverse('api_eighth_activity_list'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List blocks
        response = self.client.get(reverse('api_eighth_block_list'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # List specific block
        block = EighthBlock.objects.create(date=datetime.datetime(2015, 1, 1), block_letter='A')
        response = self.client.get(reverse('api_eighth_block_detail', kwargs={"pk": block.pk}), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # Should not be able to list profile
        response = self.client.get(reverse('api_user_myprofile_detail'), HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 403)

    def test_no_credentials_read(self):
        # Announcements should only be available to logged in users
        response = self.client.get(reverse('api_announcements_list_create'))
        self.assertEqual(response.status_code, 401)

        # Activity list should only be available to logged in users
        response = self.client.get(reverse('api_eighth_activity_list'))
        self.assertEqual(response.status_code, 401)

        # Block list should only be available to logged in users
        response = self.client.get(reverse('api_eighth_block_list'))
        self.assertEqual(response.status_code, 401)
