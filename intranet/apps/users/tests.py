# -*- coding: utf-8 -*-

from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase


class DynamicGroupTest(IonTestCase):
    """Tests creating dynamic groups."""

    def test_dynamic_groups(self):
        out = StringIO()
        with self.settings(SENIOR_GRADUATION_YEAR=9000):
            call_command('dynamic_groups', stdout=out)
        output = ["9000: 0 users", "9000: Processed", "9001: 1 users", "9001: Processed", "9002: 0 users", "9002: Processed", "9003: 0 users",
                  "9003: Processed", "Done."]
        self.assertEqual(out.getvalue().splitlines(), output)
