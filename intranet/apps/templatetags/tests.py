import contextlib
from io import StringIO

from django.core.management import call_command

from ...test.ion_test import IonTestCase


class TemplateTest(IonTestCase):
    """Tests for the templates."""

    def test_validate_templates(self):
        """Validates all the templates."""
        out = StringIO()
        with contextlib.redirect_stdout(out):
            call_command("validate_templates")
        self.assertEqual(out.getvalue().strip(), "0 errors found")
