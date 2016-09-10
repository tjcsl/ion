# -*- coding: utf-8 -*-

from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase
from .models import User
from ..groups.models import Group


class DynamicGroupTest(IonTestCase):
    """Tests creating dynamic groups."""

    def test_dynamic_groups(self):
        out = StringIO()
        with self.settings(SENIOR_GRADUATION_YEAR=2016):
            call_command('dynamic_groups', stdout=out)
        output = ["2016: 0 users", "2016: Processed", "2017: 1 users", "2017: Processed", "2018: 0 users", "2018: Processed",
                  "2019: 0 users", "2019: Processed", "Done."]
        self.assertEqual(out.getvalue().splitlines(), output)

    def test_is_superuser(self):
        user = User.objects.create(username="test1")
        group = Group.objects.get_or_create(name="admin_all")[0]
        self.assertFalse(user.is_superuser)
        user.groups.add(group)
        del user._groups_cache
        self.assertTrue(user.is_superuser)
        user.groups.remove(group)
        user._is_superuser = True
        self.assertTrue(user.is_superuser)
