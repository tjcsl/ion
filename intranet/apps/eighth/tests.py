# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Tests for the eighth module.
"""

from unittest import mock
from django.test import TestCase
from django.core.urlresolvers import reverse
from ..users.models import User
from ...db.ldap_db import LDAPConnection
from ...test.fake_ldap import MockLDAPConnection


class EighthTest(TestCase):
    def setUp(self):
        mock.patch.object(LDAPConnection, 'conn', new=MockLDAPConnection()).start()

    def tearDown(self):
        mock.patch.stopall()

    def test_add_user(self):
        """
        Tests adding a user to a EighthScheduledActivity.
        """
        user = User.get_user(username='awilliam')
        self.client.force_login(user)
        response = self.client.get(reverse('eighth_signup'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('eighth_signup'))
        # FIXME: make signup succeed
        self.assertEqual(response.status_code, 400)
