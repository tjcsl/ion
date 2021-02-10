from unittest.mock import patch

from ...test.ion_test import IonTestCase
from .views import check_emerg, get_emerg, get_emerg_result, update_emerg_cache


class EmergTestCase(IonTestCase):
    def test_emerg(self):
        with patch("intranet.apps.emerg.views.settings.EMERGENCY_MESSAGE", "test"):
            self.assertEqual((True, "test"), check_emerg())

        # I don't have a way to check the output, but at least I can call them
        check_emerg()
        get_emerg()
        get_emerg_result()
        update_emerg_cache()
