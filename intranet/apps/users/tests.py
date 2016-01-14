# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase


class DynamicGroupTest(IonTestCase):
    """
    Tests creating dynamic groups.
    """

    def test_dynamic_groups(self):
        out = StringIO()
        call_command('dynamic_groups', stdout=out)
        output = ["2016: 1 users", "2016: Processed", "2017: 0 users", "2017: Processed", "2018: 0 users",
                  "2018: Processed", "2019: 0 users", "2019: Processed", "Done."]
        self.assertEqual(out.getvalue().splitlines(), output)
