# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join
from unittest import mock
from django.test import TestCase
import ldap3

from ..apps.users.models import User
from ..db import ldap_db


class IonTestCase(TestCase):
    @classmethod
    def start_server(cls):
        cls.server = ldap3.Server('mock_server')
        cls.conn = ldap3.Connection(cls.server, client_strategy=ldap3.MOCK_SYNC)
        datadir = join(dirname(abspath(__file__)), 'data')
        cls.conn.strategy.entries_from_json(join(datadir, 'awilliam.json'))
        cls.conn.bind()
        cls.mock = mock.patch.object(ldap_db.LDAPConnection, 'conn', cls.conn)
        cls.mock.start()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.start_server()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.mock.stop()
        cls.conn.unbind()

    def login(self):
        # We need to add the user to the db before trying to login as them.
        User.get_user(username='awilliam').save()
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            self.client.login(username='awilliam', password='dankmemes')
