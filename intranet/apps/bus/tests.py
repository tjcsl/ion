# -*- coding: utf-8 -*-

from django.urls import reverse

from .models import Route
from ...test.ion_test import IonTestCase


class BusTest(IonTestCase):
    """Test for bus module"""

    def test_bus(self):
        self.login()

        self.assertEqual(self.client.get(reverse("bus")).status_code, 200)

    def test_routes(self):
        route = Route.objects.get_or_create(route_name="JT-101", bus_number="JT-101")[0]
        route.status = "a"
        route.space = "_1"
        route.save()

        route.reset_status()

        self.assertEqual(route.status, "o")
        self.assertEqual(route.space, "")
