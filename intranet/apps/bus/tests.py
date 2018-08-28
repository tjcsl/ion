# -*- coding: utf-8 -*-

from django.urls import reverse

from ...test.ion_test import IonTestCase


class BusTest(IonTestCase):
    """Test for bus module"""

    def test_bus(self):
        self.login()

        self.assertEqual(self.client.get(reverse("bus")).status_code, 200)
