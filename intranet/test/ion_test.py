from unittest import mock
from django.test import TestCase
from ..db.ldap_db import LDAPConnection

from .fake_ldap import MockLDAPConnection


class IonTestCase(TestCase):
    """
    We don't want to actually call out to ldap for testing, so mock it out here.
    """
    @classmethod
    def setUpClass(cls):
        cls.ldap_mock = mock.patch.object(LDAPConnection, 'conn', new=MockLDAPConnection()).start()

    @classmethod
    def tearDownClass(cls):
        cls.ldap_mock.stop()
