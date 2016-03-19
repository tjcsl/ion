# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase, override_settings

from ldap_test import LdapServer

from ..apps.users.models import User

mock_server = None
# We don't want to actually call out to ldap for testing, so setup a fake server.
# If we're not actually testing, then there's no point in the overhead.
if settings.TESTING:
    mock_server = LdapServer({'base': {'objectclass': 'organization', 'dn': 'dc=tjhsst,dc=edu'},
                              'ldifs': ['intranet/static/ldap/base.ldif', 'intranet/static/ldap/sample_student.ldif']})
    mock_server.start()


def get_mock_port():
    return mock_server.config['port'] if mock_server else 0


@override_settings(LDAP_SERVER='ldap://localhost:%d' % get_mock_port(), USE_SASL=False)
class IonTestCase(TestCase):

    def login(self):
        # We need to add the user to the db before trying to login as them.
        User.get_user(username='awilliam').save()
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            self.client.login(username='awilliam', password='dankmemes')
