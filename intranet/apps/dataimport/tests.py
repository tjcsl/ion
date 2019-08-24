from datetime import datetime
from io import StringIO

from django.core.management import call_command
from django.utils import timezone

from ...test.ion_test import IonTestCase


class YearCleanupTest(IonTestCase):
    """Tests end of year cleanup."""

    def test_year_cleanup(self):
        out = StringIO()
        year = timezone.now().year
        turnover_date = datetime(year, 7, 1)
        with self.settings(SENIOR_GRADUATION_YEAR=year + 1):
            call_command("year_cleanup", stdout=out)
        output = [
            "In pretend mode.",
            "Turnover date set to: {}".format(turnover_date.strftime("%c")),
            "OK: SENIOR_GRADUATION_YEAR = {} in settings/__init__.py".format(year + 1),
            "Resolving absences",
            "Updating welcome state",
            "Deleting graduated users",
            "Archiving admin comments",
        ]
        self.assertEqual(out.getvalue().splitlines(), output)
