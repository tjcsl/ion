# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase


class GrantAdminTest(IonTestCase):
    """
    Tests granting admin to an user.
    """

    def test_grant_admin(self):
        """
        Tests giving an valid user admin_all.
        """
        out = StringIO()
        call_command('grant_admin', 'awilliam', 'admin_all', stdout=out)
        self.assertEqual(out.getvalue().strip(), 'Added awilliam to admin_all')
