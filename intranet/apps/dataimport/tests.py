# -*- coding: utf-8 -*-

from datetime import datetime
from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase


class YearCleanupTest(IonTestCase):
    """Tests end of year cleanup."""

    def test_year_cleanup(self):
        out = StringIO()
        year = datetime.now().year
        with self.settings(SENIOR_GRADUATION_YEAR=year + 1):
            call_command('year_cleanup', stdout=out)
        output = [
            "In pretend mode.", "Turnover date set to: Fri Jul  1 00:00:00 2016", "OK: SENIOR_GRADUATION_YEAR = 2017 in settings/__init__.py",
            "Resolving absences", "Updating welcome state", "Deleting graduated users"
        ]
        self.assertEqual(out.getvalue().splitlines(), output)
