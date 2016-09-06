# -*- coding: utf-8 -*-

from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase


class ScheduleTest(IonTestCase):
    """Tests schedules."""

    def test_ical(self):
        out = StringIO()
        call_command('ical', stdout=out)
        output = ["{}"]
        self.assertEqual(out.getvalue().splitlines(), output)
