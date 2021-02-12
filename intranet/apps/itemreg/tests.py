from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ..groups.models import Group
from .models import CalculatorRegistration, ComputerRegistration, PhoneRegistration


class ItemRegTestCase(IonTestCase):

    """Test cases for the itemreg app."""

    def test_home_view(self):
        """Tests for home_view"""
        self.login("awilliam")
        user = get_user_model().objects.get(username="awilliam")

        # Just load the page.
        response = self.client.get(reverse("itemreg"))
        self.assertEqual(200, response.status_code)

        # Add some items, then load the page.
        phone = PhoneRegistration.objects.create(user=user, manufacturer="other", imei="351756051523999", description="A phone")
        calc = CalculatorRegistration.objects.create(user=user, calc_type="ti84p", calc_serial="9999999", calc_id="999999")
        comp = ComputerRegistration.objects.create(user=user, manufacturer="other", model="test", serial="999999999", screen_size=14)

        response = self.client.get(reverse("itemreg"))
        self.assertEqual(200, response.status_code)
        self.assertIn(phone, response.context["phones"])
        self.assertIn(calc, response.context["calculators"])
        self.assertIn(comp, response.context["computers"])

    def test_search_view(self):
        """Tests for search_view, the view to search for registered items."""
        self.login("awilliam")
        user = get_user_model().objects.get_or_create(username="awilliam")[0]
        user2 = get_user_model().objects.get_or_create(username="awilliam1")[0]

        # awilliam should be denied
        response = self.client.get(reverse("itemreg_search"))
        self.assertEqual(404, response.status_code)

        # Now, make awilliam part of the group
        group = Group.objects.get_or_create(name="admin_itemreg")[0]
        user.groups.add(group)
        user.save()

        # awilliam should now be able to load the search page
        response = self.client.get(reverse("itemreg_search"))
        self.assertEqual(200, response.status_code)

        # Now, add some items belonging to user2 (awiliam1)
        phone = PhoneRegistration.objects.create(user=user2, manufacturer="other", imei="351756051523999", description="A phone")
        calc = CalculatorRegistration.objects.create(user=user2, calc_type="ti84p", calc_serial="9999999", calc_id="999999")
        comp = ComputerRegistration.objects.create(user=user2, manufacturer="other", model="test", serial="999999999", screen_size=14)

        # Search for all items in the database
        response = self.client.get(reverse("itemreg_search"), data={"type": "all", "user": ""})
        self.assertEqual(200, response.status_code)

        self.assertIn(phone, response.context["results"]["phone"])
        self.assertIn(calc, response.context["results"]["calculator"])
        self.assertIn(comp, response.context["results"]["computer"])

        # Search by user
        response = self.client.get(reverse("itemreg_search"), data={"type": "all", "user": "awilliam1"})
        self.assertEqual(200, response.status_code)

        self.assertIn(phone, response.context["results"]["phone"])
        self.assertIn(calc, response.context["results"]["calculator"])
        self.assertIn(comp, response.context["results"]["computer"])

        # Search by phone IMEI
        response = self.client.get(reverse("itemreg_search"), data={"type": "phone", "imei": "351756051523999"})
        self.assertEqual(200, response.status_code)

        self.assertIn(phone, response.context["results"]["phone"])

        # Search by calculator serial
        response = self.client.get(reverse("itemreg_search"), data={"type": "calculator", "serial": "9999999"})
        self.assertEqual(200, response.status_code)

        self.assertIn(calc, response.context["results"]["calculator"])

        # Search by computer serial
        response = self.client.get(reverse("itemreg_search"), data={"type": "computer", "serial": "999999999"})
        self.assertEqual(200, response.status_code)

        self.assertIn(comp, response.context["results"]["computer"])

    def test_register_view(self):
        """Tests for register_view, the view to register items."""
        self.login()

        # Load the page.
        for item_type in ["computer", "calculator", "phone"]:
            response = self.client.get(reverse("itemreg_register", kwargs={"item_type": item_type}))
            self.assertEqual(200, response.status_code)

        # Register a phone.
        response = self.client.post(
            reverse("itemreg_register", kwargs={"item_type": "phone"}),
            data={"manufacturer": "other", "imei": "123456789", "model": "test", "description": "haha"},
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PhoneRegistration.objects.filter(imei="123456789").count())

        # Register a computer.
        response = self.client.post(
            reverse("itemreg_register", kwargs={"item_type": "computer"}),
            data={"manufacturer": "other", "serial": "1234567890", "model": "test", "description": "haha", "screen_size": 14},
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, ComputerRegistration.objects.filter(serial="1234567890").count())

        # Register a calculator.
        response = self.client.post(
            reverse("itemreg_register", kwargs={"item_type": "calculator"}),
            data={
                "calc_type": "ti84p",
                "calc_serial": "987654321",
                "calc_id": "test",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, CalculatorRegistration.objects.filter(calc_serial="987654321").count())

    def test_register_delete_view(self):
        """Test register_delete_view, the view to delete a registered item."""
        self.login("awilliam")
        user = get_user_model().objects.get(username="awilliam")
        phone = PhoneRegistration.objects.create(user=user, manufacturer="other", imei="351756051523999", description="A phone")
        calc = CalculatorRegistration.objects.create(user=user, calc_type="ti84p", calc_serial="9999999", calc_id="999999")
        comp = ComputerRegistration.objects.create(user=user, manufacturer="other", model="test", serial="999999999", screen_size=14)

        # Delete them
        registration_types = {CalculatorRegistration: "calculator", PhoneRegistration: "phone", ComputerRegistration: "computer"}
        for item in [phone, calc, comp]:
            self.client.post(
                reverse("itemreg_delete", kwargs={"item_type": registration_types[type(item)], "item_id": item.id}), data={"confirm": "confirm"}
            )
            self.assertEqual(0, type(item).objects.filter(id=item.id).count())
