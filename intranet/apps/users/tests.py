import datetime
import io
import os

from oauth2_provider.models import AccessToken, get_application_model
from oauth2_provider.settings import oauth2_settings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..nomination.models import Nomination, NominationPosition
from ..polls.models import Answer, Choice, Poll, Question
from .models import PERMISSIONS_NAMES, Address, Course, Email, Section

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

    def test_get_teachers(self):
        login_user = self.login()
        login_user.user_type = "student"
        login_user.save()

        users = [
            get_user_model().objects.create(
                first_name=first_name, last_name=last_name, username=first_name[0].lower() + last_name.lower()[:7], user_type="teacher"
            )
            for first_name, last_name in [
                ("Michael", "Williams"),
                ("Miguel", "Wilson"),
                ("John", "Smith"),
                ("John", "Adams"),
                ("Michael", "Adams"),
                ("Adam", "Smith"),
                ("Andrew", "Adams"),
            ]
        ]

        self.assertQuerysetEqual(get_user_model().objects.get_teachers(), list(map(repr, users)), ordered=False)

        self.assertEqual(list(get_user_model().objects.get_teachers_sorted()), sorted(users, key=lambda u: (u.last_name, u.first_name)))

        blank_user = get_user_model().objects.create(username="NOBODY", user_type="teacher")
        for first_name in [None, "", "Jack"]:
            for last_name in [None, "", "Webber"]:
                if first_name and last_name:
                    continue

                blank_user.first_name = first_name
                blank_user.last_name = last_name
                blank_user.save()
                self.assertNotIn(blank_user.id, [user.id for user in get_user_model().objects.get_teachers()])

        for user in users:
            user.delete()

    def test_name(self):
        user = self.login()
        user.username = "2000awilliam"
        user.first_name = "Andrew"
        user.last_name = "William"
        user.nickname = ""
        user.student_id = ""
        user.user_type = "student"

        self.assertEqual(user.full_name, "Andrew William")
        self.assertEqual(user.full_name_nick, "Andrew William")
        self.assertEqual(user.last_first, "William, Andrew")
        self.assertEqual(user.last_first_id, "William, Andrew (2000awilliam)")
        self.assertEqual(user.last_first_initial, "William, A.")
        self.assertEqual(user.full_name, user.display_name)
        self.assertEqual(user.full_name, user.get_full_name())
        self.assertEqual(user.first_name, user.short_name)
        self.assertEqual(user.first_name, user.get_short_name())

        user.student_id = "1234567"

        self.assertEqual(user.full_name, "Andrew William")
        self.assertEqual(user.full_name_nick, "Andrew William")
        self.assertEqual(user.last_first, "William, Andrew")
        self.assertEqual(user.last_first_id, "William, Andrew (1234567)")
        self.assertEqual(user.last_first_initial, "William, A.")
        self.assertEqual(user.full_name, user.display_name)
        self.assertEqual(user.full_name, user.get_full_name())
        self.assertEqual(user.first_name, user.short_name)
        self.assertEqual(user.first_name, user.get_short_name())

        user.student_id = ""
        user.user_type = "teacher"

        self.assertEqual(user.full_name, "Andrew William")
        self.assertEqual(user.full_name_nick, "Andrew William")
        self.assertEqual(user.last_first, "William, Andrew")
        self.assertEqual(user.last_first_id, "William, Andrew (2000awilliam)")
        self.assertEqual(user.last_first_initial, "William, A.")
        self.assertEqual(user.full_name, user.display_name)
        self.assertEqual(user.full_name, user.get_full_name())
        self.assertEqual(user.first_name, user.short_name)
        self.assertEqual(user.first_name, user.get_short_name())

        user.nickname = "Andy"

        user.student_id = ""
        user.user_type = "student"

        self.assertEqual(user.full_name, "Andrew William")
        self.assertEqual(user.full_name_nick, "Andy William")
        self.assertEqual(user.last_first, "William, Andrew (Andy)")
        self.assertEqual(user.last_first_id, "William, Andrew (Andy) (2000awilliam)")
        self.assertEqual(user.last_first_initial, "William, A. (Andy)")
        self.assertEqual(user.full_name, user.display_name)
        self.assertEqual(user.full_name, user.get_full_name())
        self.assertEqual(user.first_name, user.short_name)
        self.assertEqual(user.first_name, user.get_short_name())

        user.student_id = "1234567"

        self.assertEqual(user.full_name, "Andrew William")
        self.assertEqual(user.full_name_nick, "Andy William")
        self.assertEqual(user.last_first, "William, Andrew (Andy)")
        self.assertEqual(user.last_first_id, "William, Andrew (Andy) (1234567)")
        self.assertEqual(user.last_first_initial, "William, A. (Andy)")
        self.assertEqual(user.full_name, user.display_name)
        self.assertEqual(user.full_name, user.get_full_name())
        self.assertEqual(user.first_name, user.short_name)
        self.assertEqual(user.first_name, user.get_short_name())

        user.student_id = ""
        user.user_type = "teacher"

        self.assertEqual(user.full_name, "Andrew William")
        self.assertEqual(user.full_name_nick, "Andy William")
        self.assertEqual(user.last_first, "William, Andrew (Andy)")
        self.assertEqual(user.last_first_id, "William, Andrew (Andy) (2000awilliam)")
        self.assertEqual(user.last_first_initial, "William, A. (Andy)")
        self.assertEqual(user.full_name, user.display_name)
        self.assertEqual(user.full_name, user.get_full_name())
        self.assertEqual(user.first_name, user.short_name)
        self.assertEqual(user.first_name, user.get_short_name())

    def test_user_with_name(self):
        users = [
            get_user_model().objects.create(
                first_name=first_name, last_name=last_name, username=first_name[0].lower() + last_name.lower()[:7], user_type="teacher"
            )
            for first_name, last_name in [
                ("Michael", "Williams"),
                ("Miguel", "Wilson"),
                ("John", "Smith"),
                ("John", "Adams"),
                ("Michael", "Adams"),
                ("Adam", "Smith"),
                ("Andrew", "Adams"),
            ]
        ]

        self.assertEqual(get_user_model().objects.user_with_name("Mike", None), None)
        michael = get_user_model().objects.get(first_name="Michael", last_name="Williams")
        michael.nickname = "Mike"
        michael.save()
        self.assertEqual(get_user_model().objects.user_with_name("Mike", None).id, michael.id)

        self.assertEqual(get_user_model().objects.user_with_name("Miguel", None).last_name, "Wilson")
        self.assertEqual(get_user_model().objects.user_with_name("Miguel", None).last_name, "Wilson")
        self.assertEqual(get_user_model().objects.user_with_name("John", None), None)
        self.assertEqual(get_user_model().objects.user_with_name("Michael", None), None)
        self.assertEqual(get_user_model().objects.user_with_name("NOBODY", None), None)
        self.assertEqual(get_user_model().objects.user_with_name(None, "Adams"), None)
        self.assertEqual(get_user_model().objects.user_with_name(None, "Smith"), None)
        self.assertEqual(get_user_model().objects.user_with_name(None, "Williams").first_name, "Michael")

        for user in users:
            user.delete()

    def test_notification_email(self):
        # Test default user notification email property
        user = self.login()
        user.primary_email = None
        user.save()
        user.emails.all().delete()

        self.assertEqual(user.primary_email, None)
        self.assertFalse(user.emails.exists())
        self.assertEqual(user.tj_email, "{}@tjhsst.edu".format(user.username))
        self.assertEqual(user.notification_email, user.tj_email)

        email = Email.objects.create(user=user, address="test@example.com")
        self.assertEqual(user.notification_email, email.address)

        # Set primary email
        user.primary_email = Email.objects.create(user=user, address="test2@example.com")
        user.save()
        self.assertEqual(user.notification_email, user.primary_email_address)

    def test_has_unvoted_polls(self):
        user = self.login()

        self.assertFalse(user.has_unvoted_polls())

        ago_5 = timezone.localtime() - datetime.timedelta(minutes=5)
        future_5 = timezone.localtime() + datetime.timedelta(minutes=5)

        poll = Poll.objects.create(title="Test", description="Test", start_time=ago_5, end_time=ago_5, visible=False)
        # Happened in the past, not visible
        self.assertFalse(user.has_unvoted_polls())

        # Happened in the past, visible
        poll.visible = True
        poll.save()
        self.assertFalse(user.has_unvoted_polls())

        # Happening in the future, visible
        poll.start_time = future_5
        poll.end_time = future_5
        poll.save()
        self.assertFalse(user.has_unvoted_polls())

        # Happening in the future, not visible
        poll.visible = False
        poll.save()
        self.assertFalse(user.has_unvoted_polls())

        # Happening now, not visible
        poll.start_time = ago_5
        poll.end_time = future_5
        poll.save()
        self.assertFalse(user.has_unvoted_polls())

        # Happening now, visible
        poll.visible = True
        poll.save()
        self.assertTrue(user.has_unvoted_polls())

        # Add a question and an answer choice
        ques1 = Question.objects.create(poll=poll, question="TEST", num=1, type=Question.STD, max_choices=1)
        self.assertTrue(user.has_unvoted_polls())
        choice1 = Choice.objects.create(question=ques1, num=1, info="TEST CHOICE")
        self.assertTrue(user.has_unvoted_polls())

        # Now answer it
        Answer.objects.create(question=ques1, user=user, choice=choice1)
        self.assertFalse(user.has_unvoted_polls())

        # Add another question (this should NOT make the poll unanswered, because we just check if the user has answered any of the poll's questions)
        ques2 = Question.objects.create(poll=poll, question="TEST 2", num=2, type=Question.STD, max_choices=1)
        self.assertFalse(user.has_unvoted_polls())
        choice2 = Choice.objects.create(question=ques2, num=1, info="TEST CHOICE")
        self.assertFalse(user.has_unvoted_polls())

        # Answer it
        Answer.objects.create(question=ques2, user=user, choice=choice2)
        self.assertFalse(user.has_unvoted_polls())

        poll.delete()

    def test_signed_up_today(self):
        user = self.login()
        user.user_type = "student"
        user.save()

        EighthBlock.objects.all().delete()

        self.assertTrue(user.signed_up_today())

        block = EighthBlock.objects.create(date=timezone.localdate() - datetime.timedelta(days=1), block_letter="A")
        act = EighthActivity.objects.create(name="Test activity 1")
        schact = EighthScheduledActivity.objects.create(activity=act, block=block)

        self.assertTrue(user.signed_up_today())

        block.date = timezone.localdate()
        block.save()

        self.assertFalse(user.signed_up_today())

        EighthSignup.objects.create(user=user, scheduled_activity=schact)

        self.assertTrue(user.signed_up_today())

        block.delete()
        act.delete()

    def test_signed_up_next_few_days(self):
        user = self.login()
        user.user_type = "student"
        user.save()

        EighthBlock.objects.all().delete()

        act = EighthActivity.objects.create(name="Test activity 1")

        today = timezone.localdate()

        self.assertTrue(user.signed_up_next_few_days())
        self.assertTrue(user.signed_up_next_few_days(num_days=3))
        self.assertTrue(user.signed_up_next_few_days(num_days=2))
        self.assertTrue(user.signed_up_next_few_days(num_days=1))

        for d in [3, -1]:
            EighthScheduledActivity.objects.create(
                activity=act, block=EighthBlock.objects.create(date=today + datetime.timedelta(days=d), block_letter="A")
            )

            self.assertTrue(user.signed_up_next_few_days())
            self.assertTrue(user.signed_up_next_few_days(num_days=3))
            self.assertTrue(user.signed_up_next_few_days(num_days=2))
            self.assertTrue(user.signed_up_next_few_days(num_days=1))

        for d in [2, 1, 0]:
            schact_a = EighthScheduledActivity.objects.create(
                activity=act, block=EighthBlock.objects.create(date=today + datetime.timedelta(days=d), block_letter="A")
            )

            self.assertFalse(user.signed_up_next_few_days())
            for j in range(d + 1, 5):
                self.assertFalse(user.signed_up_next_few_days(num_days=j))
            for j in range(1, d + 1):
                self.assertTrue(user.signed_up_next_few_days(num_days=j))

            EighthSignup.objects.create(user=user, scheduled_activity=schact_a)

            self.assertTrue(user.signed_up_next_few_days())
            self.assertTrue(user.signed_up_next_few_days(num_days=3))
            self.assertTrue(user.signed_up_next_few_days(num_days=2))
            self.assertTrue(user.signed_up_next_few_days(num_days=1))

            schact_b = EighthScheduledActivity.objects.create(
                activity=act, block=EighthBlock.objects.create(date=today + datetime.timedelta(days=d), block_letter="B")
            )

            self.assertFalse(user.signed_up_next_few_days())
            for j in range(d + 1, 5):
                self.assertFalse(user.signed_up_next_few_days(num_days=j))
            for j in range(1, d + 1):
                self.assertTrue(user.signed_up_next_few_days(num_days=j))

            EighthSignup.objects.create(user=user, scheduled_activity=schact_b)

            self.assertTrue(user.signed_up_next_few_days())
            self.assertTrue(user.signed_up_next_few_days(num_days=3))
            self.assertTrue(user.signed_up_next_few_days(num_days=2))
            self.assertTrue(user.signed_up_next_few_days(num_days=1))

        EighthBlock.objects.all().delete()

        # Teachers are never "not signed up"
        user.user_type = "teacher"
        user.save()
        EighthScheduledActivity.objects.create(activity=act, block=EighthBlock.objects.create(date=today, block_letter="A"))
        self.assertTrue(user.signed_up_next_few_days())
        self.assertTrue(user.signed_up_next_few_days(num_days=3))
        self.assertTrue(user.signed_up_next_few_days(num_days=2))
        self.assertTrue(user.signed_up_next_few_days(num_days=1))

    def test_tj_email_non_tj_email(self):
        user = self.login()
        user.primary_email = None
        user.save()
        user.emails.all().delete()

        self.assertEqual(user.primary_email, None)
        self.assertFalse(user.emails.exists())
        self.assertEqual(user.tj_email, "{}@tjhsst.edu".format(user.username))
        self.assertEqual(user.non_tj_email, None)

        personal_email = Email.objects.create(user=user, address="abc@example.com")
        self.assertEqual(user.tj_email, "{}@tjhsst.edu".format(user.username))
        self.assertEqual(user.non_tj_email, personal_email.address)

        user.user_type = "teacher"
        user.save()
        self.assertEqual(user.tj_email, "{}@fcps.edu".format(user.username))
        self.assertEqual(user.non_tj_email, personal_email.address)
        user.user_type = "student"
        user.save()

        email_tj = Email.objects.create(user=user, address="jsmith@tjhsst.edu")
        self.assertEqual(user.tj_email, email_tj.address)
        self.assertEqual(user.non_tj_email, personal_email.address)
        email_tj.delete()

        email_fcps = Email.objects.create(user=user, address="jsmith@fcps.edu")
        self.assertEqual(user.tj_email, email_fcps.address)
        self.assertEqual(user.non_tj_email, personal_email.address)
        email_fcps.delete()

        personal_email.delete()

        email_tj = Email.objects.create(user=user, address="jsmith@tjhsst.edu")
        self.assertEqual(user.tj_email, email_tj.address)
        self.assertEqual(user.non_tj_email, None)
        email_tj.delete()

        email_fcps = Email.objects.create(user=user, address="jsmith@fcps.edu")
        self.assertEqual(user.tj_email, email_fcps.address)
        self.assertEqual(user.non_tj_email, None)
        email_fcps.delete()

    def test_male_female(self):
        """Tests all possible values of is_male/is_female."""
        user = self.login()

        user.gender = None
        self.assertFalse(user.is_male)
        self.assertFalse(user.is_female)

        user.gender = True
        self.assertTrue(user.is_male)
        self.assertFalse(user.is_female)

        user.gender = False
        self.assertFalse(user.is_male)
        self.assertTrue(user.is_female)


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
        address = self.user.properties._address  # pylint: disable=protected-access
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

        with self.settings(YEAR_TURNOVER_MONTH=(timezone.localtime() + timezone.timedelta(days=70)).month):
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
            self.assertEqual(set(PERMISSIONS_NAMES[k]), {"show_pictures", "show_address", "show_telephone", "show_eighth", "show_schedule"})

        self.assertEqual(set(self.user.permissions.keys()), {"self", "parent"})
        for k in ["self", "parent"]:
            self.assertEqual(
                set(self.user.permissions[k].keys()), {"show_pictures", "show_address", "show_telephone", "show_eighth", "show_schedule"},
            )
