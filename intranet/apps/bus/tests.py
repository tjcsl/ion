import datetime
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from .models import Route


class BusTest(IonTestCase):
    """Test for bus module"""

    def test_bus(self):
        self.login()

        # Test morning
        morning_tz = timezone.make_aware(datetime.datetime(3000, 1, 1, hour=settings.BUS_PAGE_CHANGEOVER_HOUR - 1, minute=0, second=0))
        with patch("django.utils.timezone.localtime", return_value=morning_tz) as m:
            response = self.client.get(reverse("bus"))
            self.assertEqual(response.status_code, 200)

            self.assertTemplateUsed(response, template_name="bus/morning.html")

        m.assert_called()

        # Test afternoon
        afternoon_tz = timezone.make_aware(datetime.datetime(3000, 1, 1, hour=settings.BUS_PAGE_CHANGEOVER_HOUR + 1, minute=0, second=0))
        with patch("django.utils.timezone.localtime", return_value=afternoon_tz) as m:
            response = self.client.get(reverse("bus"))
            self.assertEqual(response.status_code, 200)

            self.assertTemplateUsed(response, template_name="bus/home.html")

        m.assert_called()

    def test_routes(self):
        route = Route.objects.get_or_create(route_name="JT-01", bus_number="JT-01")[0]
        route.status = "a"
        route.space = "_1"
        route.save()

        route.reset_status()

        self.assertEqual(route.status, "o")
        self.assertEqual(route.space, "")

    def test_route_representation(self):
        route = Route.objects.get_or_create(route_name="JT-01", bus_number="JT-01")[0]
        route_str = str(route)

        self.assertEqual(route.route_name, route_str)
