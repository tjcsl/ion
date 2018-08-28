# -*- coding: utf-8 -*-

from io import StringIO

from django.urls import reverse
from django.core.management import call_command

from ..users.models import User
from ...test.ion_test import IonTestCase
from .backends import KerberosAuthenticationBackend, MasterPasswordAuthenticationBackend


class GrantAdminTest(IonTestCase):
    """Tests granting admin to an user."""

    def test_grant_admin(self):
        """Tests giving an valid user admin_all."""
        out = StringIO()
        call_command('grant_admin', 'awilliam', 'admin_all', stdout=out)
        self.assertEqual(out.getvalue().strip(), 'Added awilliam to admin_all')


class LoginViewTest(IonTestCase):
    """Tests of the login page (but not actually auth)"""

    def test_login_page(self):
        self.assertEqual(self.client.get(reverse("index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("about")).status_code, 200)
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_authentication(self):
        User.objects.get_or_create(username="awilliam")
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            response = self.client.post(reverse("index"), data={
                "username": "awilliam",
                "password": "dankmemes"
            })

        self.assertEqual(response.status_code, 200)

    def test_authentication_first_time(self):
        user = User.objects.get_or_create(username="awilliam")[0]
        user.first_login = False
        with self.settings(MASTER_PASSWORD='pbkdf2_sha256$24000$qp64pooaIEAc$j5wiTlyYzcMu08dVaMRus8Kyfvn5ZfaJ/Rn+Z/fH2Bw='):
            response = self.client.post(reverse("index"), data={
                "username": "awilliam",
                "password": "dankmemes"
            })

        self.assertEqual(response.status_code, 200)

    def test_get_user(self):
        user = User.objects.get_or_create(username="awilliam")[0]
        self.assertEqual(KerberosAuthenticationBackend.get_user(user.id),
                         user)
        self.assertIsNone(KerberosAuthenticationBackend.get_user(1000))
        self.assertEqual(MasterPasswordAuthenticationBackend.get_user(user.id),
                         user)
        self.assertIsNone(MasterPasswordAuthenticationBackend.get_user(1000))
