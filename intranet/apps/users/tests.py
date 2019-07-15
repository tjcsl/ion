import datetime
import io
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import get_application_model, AccessToken
from oauth2_provider.settings import oauth2_settings

from .models import PERMISSIONS_NAMES, Address, Course, Section
from ..eighth.models import EighthBlock, EighthActivity, EighthScheduledActivity, EighthSignup
from ..nomination.models import Nomination, NominationPosition
from ...test.ion_test import IonTestCase

Application = get_application_model()


class CourseTest(IonTestCase):
    def setUp(self):
        self.create_schedule_test()

    def create_schedule_test(self):
        for i in range(9):
            course = Course.objects.create(name="Test Course {}".format(i), course_id="1111{}".format(i))
            for pd in range(1, 8):
                Section.objects.create(course=course, room="Room {}".format(i), period=pd, section_id="{}-{}".format(course.course_id, pd), sem="F")

    def test_section_course_attributes(self):
        course = Course.objects.first()
        self.assertEqual(str(course), "{} ({})".format(course.name, course.course_id))

        section = Section.objects.first()
        self.assertEqual(str(section), "{} ({}) - {} Pd. {}".format(section.course.name, section.section_id, "Unknown", section.period))

    def test_all_courses_view(self):
        _ = self.login()
        response = self.client.get(reverse("all_courses"))
        self.assertTemplateUsed(response, "users/all_courses.html")
        self.assertEqual(list(response.context["courses"]), list(Course.objects.all().order_by("name", "course_id").distinct()))

    def test_courses_by_period_view(self):
        _ = self.login()
        pd = 2
        response = self.client.get(reverse("period_courses", args=[pd]))
        self.assertTemplateUsed(response, "users/all_courses.html")
        self.assertEqual(list(response.context["courses"]), list(Course.objects.filter(sections__period=pd).order_by("name", "course_id").distinct()))

    def test_course_info_view(self):
        _ = self.login()
        # Test invalid course
        course_id = "BAD"
        response = self.client.get(reverse("course_sections", args=[course_id]))
        self.assertEqual(response.status_code, 404)

        # Test valid course
        course_id = "11110"
        response = self.client.get(reverse("course_sections", args=[course_id]))
        self.assertTemplateUsed(response, "users/all_classes.html")
        self.assertEqual(response.context["course"], Course.objects.get(course_id=course_id))

    def test_sections_by_room_view(self):
        _ = self.login()
        # Test room with no sections
        response = self.client.get(reverse("room_sections", args=["BAD"]))
        self.assertEqual(response.status_code, 404)

        # Test valid room
        room_number = "Room 1"
        response = self.client.get(reverse("room_sections", args=[room_number]))
        self.assertTemplateUsed(response, "users/class_room.html")
        self.assertEqual(response.context["room_number"], room_number)
        self.assertEqual(list(response.context["classes"]), list(Section.objects.filter(room=room_number).order_by("period")))

    def test_section_view(self):
        _ = self.login()

        # Test invalid section
        response = self.client.get(reverse("section_info", args=["BAD"]))
        self.assertEqual(response.status_code, 404)

        # Test valid section
        section = Section.objects.first()
        response = self.client.get(reverse("section_info", args=[section.section_id]))
        self.assertTemplateUsed(response, "users/class.html")
        self.assertEqual(response.context["class"], section)


class UserTest(IonTestCase):
    def test_get_signage_user(self):
        self.assertEqual(get_user_model().get_signage_user().id, 99999)


class ProfileTest(IonTestCase):
    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username="awilliam")[0]
        address = Address.objects.get_or_create(street="6560 Braddock Rd", city="Alexandria", state="VA", postal_code="22312")[0]
        self.user.properties._address = address  # pylint: disable=protected-access
        self.user.properties.save()
        self.user.save()
        self.application = Application(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        self.application.save()

        self.client_credentials_application = Application(
            name="Test Client Credentials Application",
            redirect_uris="http://localhost http://example.com http://example.it",
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        self.client_credentials_application.save()

        oauth2_settings._SCOPES = ["read", "write"]  # pylint: disable=protected-access

    def make_token(self):
        tok = AccessToken.objects.create(
            user=self.user, token="1234567890", application=self.application, scope="read write", expires=timezone.now() + datetime.timedelta(days=1)
        )
        self.auth = "Bearer {}".format(tok.token)  # pylint: disable=attribute-defined-outside-init

    def test_get_profile_api(self):
        self.make_admin()
        self.make_token()

        # Check for non-existent user.
        response = self.client.get(reverse("api_user_profile_detail", args=[9999]), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 404)

        # Get data for ourself.
        response = self.client.get(reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 200)
        address = self.user.properties._address
        self.assertEqual(response.json()["address"]["postal_code"], address.postal_code)
        self.assertEqual(response.json()["address"]["street"], address.street)
        self.assertEqual(response.json()["address"]["city"], address.city)
        self.assertEqual(response.json()["address"]["state"], address.state)

        # Verify that response is the same
        response_with_username = self.client.get(
            reverse("api_user_myprofile_detail") + "?username={}".format(self.user.username), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response_with_username.json(), response.json())
        response_with_pk = self.client.get(reverse("api_user_myprofile_detail") + "?pk={}".format(self.user.pk), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response_with_pk.json(), response.json())

    def test_get_profile_picture_api(self):
        user = self.login()
        self.make_token()

        # Test with no pictures attached on default
        response = self.client.get(reverse("api_user_profile_picture_default", args=[user.pk]), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.content_type, "image/jpeg")
        image_path = os.path.join(settings.PROJECT_ROOT, "static/img/default_profile_pic.png")
        self.assertEqual(response.content, io.open(image_path, mode="rb").read())
        response_with_username = self.client.get(
            reverse("api_user_profile_picture_default_by_username", args=[user.username]), HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response.content, response_with_username.content)

    def test_profile_view(self):
        user = self.login()

        # Test very plain view of own profile
        response = self.client.get(reverse("user_profile"))
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertEqual(response.context["eighth_schedule"], [])

        act = EighthActivity.objects.create(name="Test Activity")

        for day_delta in range(1, 5):
            for block in ["A", "B"]:
                block = EighthBlock.objects.create(date=(timezone.now() + timezone.timedelta(days=day_delta)).date(), block_letter=block)
                EighthScheduledActivity.objects.create(activity=act, block=block)

        # Test as a normal student accessing own profile
        response = self.client.get(reverse("user_profile"))
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertEqual(response.context["profile_user"], user)
        expected_schedule = []
        for block in list(EighthBlock.objects.order_by("date"))[:6]:
            expected_schedule.append({"block": block, "signup": None})
        self.assertEqual(response.context["eighth_schedule"], expected_schedule)
        self.assertTrue(response.context["can_view_eighth"])
        self.assertFalse(response.context["eighth_restricted_msg"])
        self.assertEqual(response.context["eighth_sponsor_schedule"], None)
        self.assertFalse(response.context["nominations_active"])
        self.assertEqual(response.context["nomination_position"], settings.NOMINATION_POSITION)
        self.assertFalse(response.context["has_been_nominated"])

        for schact in EighthScheduledActivity.objects.all():
            EighthSignup.objects.create(scheduled_activity=schact, user=user)

        response = self.client.get(reverse("user_profile"))
        expected_schedule = []
        for block in list(EighthBlock.objects.order_by("date"))[:6]:
            expected_schedule.append({"block": block, "signup": EighthSignup.objects.get(scheduled_activity__block=block)})
        self.assertEqual(response.context["eighth_schedule"], expected_schedule)

        # Test self-nomination
        position = NominationPosition.objects.create(position_name=settings.NOMINATION_POSITION)
        Nomination.objects.create(nominator=user, nominee=user, position=position)
        with self.settings(NOMINATIONS_ACTIVE=True):
            response = self.client.get(reverse("user_profile"))
            self.assertTrue(response.context["has_been_nominated"])
            self.assertTrue(response.context["nominations_active"])
            self.assertEqual(response.context["nomination_position"], settings.NOMINATION_POSITION)

    def test_privacy_options(self):
        self.assertEqual(set(PERMISSIONS_NAMES.keys()), {"self", "parent"})
        for k in ["self", "parent"]:
            self.assertEqual(
                set(PERMISSIONS_NAMES[k]), {"show_pictures", "show_address", "show_telephone", "show_birthday", "show_eighth", "show_schedule"}
            )

        self.assertEqual(set(self.user.permissions.keys()), {"self", "parent"})
        for k in ["self", "parent"]:
            self.assertEqual(
                set(self.user.permissions[k].keys()),
                {"show_pictures", "show_address", "show_telephone", "show_birthday", "show_eighth", "show_schedule"},
            )
