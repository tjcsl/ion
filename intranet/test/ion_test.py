# -*- coding: utf-8 -*-
from django.test import TestCase

from ..apps.users.models import User
from ..apps.groups.models import Group


class IonTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def login(self):
        # We need to add the user to the db before trying to login as them.
        User.objects.get_or_create(username='awilliam')
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            self.client.login(username='awilliam', password='dankmemes')

    def make_admin(self):
        self.login()
        # Make user an eighth admin
        user = User.objects.get_or_create(username='awilliam')[0]
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)
        return user
