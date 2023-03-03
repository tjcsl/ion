from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..bus.models import Route
from ..users.models import Email, Phone, Photo, User, UserProperties, Website
from .forms import EmailForm
from .views import get_personal_info, get_privacy_options, save_bus_route


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
        user = self.login()
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
        response = self.client.post(reverse("preferences"), settings_dict, follow=True)
        self.assertEqual(200, response.status_code)

        # Add a photo and try to set it as preferred
        photo = Photo.objects.create(grade_number=9, user=user)
        settings_dict.update({"preferred_photo": 9})
        response = self.client.post(reverse("preferences"), settings_dict, follow=True)
        self.assertEqual(200, response.status_code)

        user = get_user_model().objects.get(username="awilliam")
        self.assertEqual(photo, user.preferred_photo)

        # Set it back to auto
        settings_dict.update({"preferred_photo": "AUTO"})
        response = self.client.post(reverse("preferences"), settings_dict, follow=True)
        self.assertEqual(200, response.status_code)

        user = get_user_model().objects.get(username="awilliam")
        self.assertIsNone(user.preferred_photo)

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

    def test_get_personal_info(self):
        # Make a user
        user = User.objects.get_or_create(username="awilliam1")[0]

        # Add some details
        phone = Phone.objects.create(user=user, purpose="m", _number="5551231234")
        phone2 = Phone.objects.create(user=user, purpose="h", _number="5551243245")

        email = Email.objects.create(user=user, address="test@example.com")

        website = Website.objects.create(user=user, url="www.example.com")

        # There are two phones, one email, and one website
        personal_info, num_fields = get_personal_info(user)

        self.assertEqual({"phones": 2, "emails": 1, "websites": 1}, num_fields)

        # It is unpredictable which order the phones appear in, so this will do
        for user_object in [phone, phone2, email, website]:
            self.assertIn(user_object, personal_info.values())

        # Then, check the email and the website
        self.assertEqual(email, personal_info["email_0"])
        self.assertEqual(website, personal_info["website_0"])

    def test_privacy_options_view(self):
        """Test the get privacy options views and associated methods."""
        user_student = User.objects.get_or_create(username="awilliam1", user_type="student", student_id=12345)[0]

        # Start by testing the get_privacy_options method
        options = get_privacy_options(user_student)

        PERMISSIONS_NAMES = {
            prefix: [name[len(prefix) + 1:] for name in dir(UserProperties) if name.startswith(prefix + "_")] for prefix in ["self", "parent"]
        }

        for permission_type in PERMISSIONS_NAMES.keys():
            for permission in PERMISSIONS_NAMES[permission_type]:
                if permission_type == "self":
                    self.assertIn(f"{permission}-{permission_type}", options.keys())
                    self.assertFalse(options[f"{permission}-{permission_type}"])
                else:
                    self.assertIn(f"{permission}", options.keys())
                    self.assertFalse(options[f"{permission}"])

        # Now, test loading the view
        user = self.login()

        user.user_type = "teacher"
        user.save()

        # This should fail b/c we're not an admin
        response = self.client.get(reverse("privacy_options"))
        self.assertEqual(302, response.status_code)  # to login page

        self.make_admin()

        # Now, this should load
        response = self.client.get(reverse("privacy_options"))
        self.assertEqual(200, response.status_code)

        # However, since `awilliam` is not a student, this should have
        # "Student not found" in the response
        self.assertIn("Student not found", str(response.content))

        # Load awilliam1's preferences
        # first, by Ion ID
        response = self.client.get(reverse("privacy_options"), data={"user": user_student.id})
        self.assertEqual(200, response.status_code)
        self.assertIn("12345", str(response.content))

        # now, by student ID
        response = self.client.get(reverse("privacy_options"), data={"student_id": user_student.student_id})
        self.assertEqual(200, response.status_code)
        self.assertIn("12345", str(response.content))

        # Try saving the form
        response = self.client.post(
            reverse("privacy_options") + f"?student_id={user_student.student_id}",
            data={
                "show_address": True,
                "show_address-self": True,
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("12345", str(response.content))

        user_student_properties = UserProperties.objects.get(user=user_student)
        self.assertTrue(user_student_properties.parent_show_address)
        self.assertTrue(user_student_properties.self_show_address)

        # Assert the rest are still false
        self.assertFalse(user_student_properties.parent_show_schedule)
        self.assertFalse(user_student_properties.parent_show_pictures)
        self.assertFalse(user_student_properties.parent_show_eighth)
        self.assertFalse(user_student_properties.parent_show_telephone)

        self.assertFalse(user_student_properties.self_show_schedule)
        self.assertFalse(user_student_properties.self_show_pictures)
        self.assertFalse(user_student_properties.self_show_eighth)
        self.assertFalse(user_student_properties.self_show_telephone)


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
