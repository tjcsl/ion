# -*- coding: utf-8 -*-
from unittest import mock

from django.test import TestCase

from .fake_ldap import MockLDAPConnection
from ..apps.users.models import User
from ..db.ldap_db import LDAPConnection


class IonTestCase(TestCase):
    def login(self):
        # We need to add the user to the db before trying to login as them.
        User.get_user(username='awilliam').save()
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            self.client.login(username='awilliam', password='dankmemes')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # We don't want to actually call out to ldap for testing, so mock it out here.
        cls.ldap_mock = mock.patch.object(LDAPConnection, 'conn', new=MockLDAPConnection()).start()

    @classmethod
    def tearDownClass(cls):
        cls.ldap_mock.stop()
        super().tearDownClass()
