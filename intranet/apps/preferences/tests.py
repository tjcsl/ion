from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..bus.models import Route
from .forms import EmailForm
from .views import save_bus_route


class PreferencesTest(IonTestCase):
    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username="awilliam", id="99999", graduation_year=get_senior_graduation_year() + 1)[0]
        route_names = ["JT-002", "JT-001"]
        for route_name in route_names:
            Route.objects.get_or_create(route_name=route_name, space="", bus_number="")
        self.route_names = sorted(route_names)
        self.factory = RequestFactory()

    def test_get_preferences(self):
        self.login()
        response = self.client.get(reverse("preferences"))
        self.assertEqual(response.status_code, 200)

    def test_set_preferences(self):
        self.login()
        settings_dict = {
            "pf-TOTAL_FORMS": ["1"],
            "ef-0-user": ["99999"],
            "pf-0-number": ["555-555-5555"],
            "wf-INITIAL_FORMS": ["0"],
            "pf-0-id": [""],
            "wf-MAX_NUM_FORMS": ["1000"],
            "ef-MIN_NUM_FORMS": ["0"],
            "wf-TOTAL_FORMS": ["1"],
            "ef-TOTAL_FORMS": ["1"],
            "wf-MIN_NUM_FORMS": ["0"],
            "pf-MIN_NUM_FORMS": ["0"],
            "pf-INITIAL_FORMS": ["0"],
            "ef-0-id": [""],
            "preferred_photo": ["AUTO"],
            "ef-0-address": ["awilliam@tjhsst.edu"],
            "show_pictures-self": ["on"],
            "ef-INITIAL_FORMS": ["0"],
            "pf-0-purpose": ["h"],
            "ef-MAX_NUM_FORMS": ["1000"],
            "receive_push_notifications": ["on"],
            "wf-0-url": ["http://ion.tjhsst.edu/logout"],
            "wf-0-id": [""],
            "pf-0-user": ["99999"],
            "wf-0-user": ["99999"],
            "pf-MAX_NUM_FORMS": ["1000"],
            "show_pictures": ["on"],
            "bus_route": ["JT-001"],
        }
        response = self.client.post(reverse("preferences"), settings_dict)
        self.assertEqual(response.status_code, 302)

    def test_clear_preferences(self):
        self.login()
        pref_dict = {
            "pf-1-number": [""],
            "pf-1-id": [""],
            "pf-0-number": ["555-555-5555"],
            "pf-0-id": ["12"],
            "wf-MAX_NUM_FORMS": ["1000"],
            "ef-MIN_NUM_FORMS": ["0"],
            "wf-TOTAL_FORMS": ["2"],
            "wf-MIN_NUM_FORMS": ["0"],
            "pf-1-purpose": ["o"],
            "wf-0-id": ["4"],
            "pf-TOTAL_FORMS": ["2"],
            "wf-0-url": ["http://ion.tjhsst.edu/logout"],
            "wf-1-user": ["99999"],
            "pf-0-DELETE": ["on"],
            "ef-1-id": [""],
            "wf-0-DELETE": ["on"],
            "pf-MAX_NUM_FORMS": ["1000"],
            "wf-0-user": ["99999"],
            "ef-1-address": [""],
            "ef-0-user": ["99999"],
            "pf-1-user": ["99999"],
            "ef-TOTAL_FORMS": ["2"],
            "pf-MIN_NUM_FORMS": ["0"],
            "pf-INITIAL_FORMS": ["1"],
            "ef-0-id": ["10"],
            "wf-1-url": [""],
            "preferred_photo": ["AUTO"],
            "ef-0-address": ["awilliam@tjhsst.edu"],
            "ef-INITIAL_FORMS": ["1"],
            "pf-0-purpose": ["h"],
            "ef-MAX_NUM_FORMS": ["1000"],
            "wf-1-id": [""],
            "wf-INITIAL_FORMS": ["1"],
            "ef-0-DELETE": ["on"],
            "pf-0-user": ["99999"],
            "ef-1-user": ["99999"],
            "show_pictures": ["on"],
            "bus_route": [""],
        }
        with self.assertLogs("intranet.apps.preferences.views", "DEBUG") as logger:
            response = self.client.post(reverse("preferences"), pref_dict)
        self.assertNotEqual(
            logger.output,
            [
                "DEBUG:intranet.apps.preferences.views:Unable to set field phones with value []"
                ": Can not set User attribute 'phones' -- not in user attribute list."
            ],
        )
        for line in logger.output:
            self.assertFalse("Error processing Bus Route Form" in line)
        self.assertEqual(response.status_code, 302)

    def test_save_bus_route(self):

        # Test that save_bus_route() works

        # Test that choices are in order
        request = self.factory.get(reverse("preferences"))
        form = save_bus_route(request, self.user)
        choices = form.fields["bus_route"].choices[1:]
        self.assertEqual(len(choices), len(self.route_names))
        for index, route_name in enumerate(self.route_names):
            self.assertEqual(route_name, choices[index][0])
            self.assertEqual(choices[index][1], choices[index][0])


class PreferencesFormTest(IonTestCase):
    def test_email_form(self):
        # Indirect test of formset validation

        _ = self.login()

        # Test valid address
        form_params = {"address": "test@example.com"}
        form = EmailForm(form_params)
        self.assertTrue(form.is_valid())

        # Test invalid address
        form_params = {"address": "test@fcpsschools.net"}
        form = EmailForm(form_params)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("address", code="invalid"))
