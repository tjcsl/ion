from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..apps.groups.models import Group
from ..apps.users.models import User


class IonTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def login(self, username: str = "awilliam") -> User:
        """
        Log the test client in as the given user.

        Args:
            username: the username to log in as

        Return:
            the ``User`` object corresponding to ``username``
        """
        # We need to add the user to the db before trying to login as them.
        user = get_user_model().objects.get_or_create(username=username)[0]
        with self.settings(MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw="):
            self.client.login(username=username, password="dankmemes")
        return user

    def reauth(self) -> None:
        """
        Reauthenticate the already logged in user.
        """

        with self.settings(MASTER_PASSWORD="pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw="):
            response = self.client.post(reverse("reauth"), data={"password": "dankmemes"})
            self.assertEqual(302, response.status_code)

    def make_admin(self, username: str = "awilliam") -> User:
        """
        Log in the test client as the given user, and make that
        user an admin (i.e. give it the admin_all group).

        Args:
            username: the username to log in as and make an admin

        Return:
            the ``User`` object corresponding to ``username``
        """
        user = self.login(username=username)
        # Make user an eighth admin
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)
        return user
