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
        call_command("year_cleanup", stdout=out, senior_grad_year=year + 1)
        output = [
            "In pretend mode.",
            "Turnover date set to: {}".format(turnover_date.strftime("%c")),
            "OK: senior_grad_year = {}".format(year + 1),
            "Resolving absences",
            "Updating welcome state",
            "Deleting graduated users",
            "Archiving admin comments",
        ]
        self.assertEqual(out.getvalue().splitlines(), output)
