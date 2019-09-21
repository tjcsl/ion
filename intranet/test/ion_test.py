from django.contrib.auth import get_user_model
from django.test import TestCase

from ..apps.groups.models import Group


class IonTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def login(self, username="awilliam"):
        # We need to add the user to the db before trying to login as them.
        user = get_user_model().objects.get_or_create(username=username)[0]
        with self.settings(MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw="):
            self.client.login(username=username, password="dankmemes")
        return user

    def make_admin(self, username="awilliam"):
        user = self.login(username=username)
        # Make user an eighth admin
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)
        return user
