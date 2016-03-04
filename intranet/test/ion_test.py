# -*- coding: utf-8 -*-
from django.test import TestCase, override_settings

from ..apps.users.models import User

from ldap_test import LdapServer

# We don't want to actually call out to ldap for testing, so setup a fake server.
mock_server = LdapServer({'base': {'objectclass': 'organization', 'dn': 'dc=tjhsst,dc=edu'},
                          'ldifs': ['intranet/static/ldap/base.ldif', 'intranet/static/ldap/sample_student.ldif']})
mock_server.start()


@override_settings(LDAP_SERVER='ldap://localhost:%d' % mock_server.config['port'])
class IonTestCase(TestCase):

    def login(self):
        # We need to add the user to the db before trying to login as them.
        User.get_user(username='awilliam').save()
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            self.client.login(username='awilliam', password='dankmemes')
