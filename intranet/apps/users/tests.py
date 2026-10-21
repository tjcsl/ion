import datetime
import os
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import AccessToken, get_application_model
from oauth2_provider.settings import oauth2_settings

from ...test.ion_test import IonTestCase
from ..eighth.models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..nomination.models import Nomination, NominationPosition
from ..oauth.validators import IonOIDCValidator
from ..polls.models import Answer, Choice, Poll, Question
from .models import PERMISSIONS_NAMES, Address, Course, Email, Section

Application = get_application_model()


class ArchiveUsersTest(IonTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username="archive_me", admin_comments="Keep these comments")
        self.locked = get_user_model().objects.create(username="already_locked", user_locked=True, admin_comments="Already archived")
        self.other = get_user_model().objects.create(username="leave_me")
        self.users = get_user_model().objects.filter(pk__in=[self.user.pk, self.locked.pk])

    def run_command(self, contents, *args):
        out = StringIO()
        with TemporaryDirectory() as directory:
            filename = Path(directory) / "users.csv"
            filename.write_text(contents, encoding="utf-8")
            call_command("archive_users", "--filename", str(filename), *args, stdout=out)
        return out.getvalue()

    def test_archive_queryset_preserves_users_and_is_repeatable(self):
        # Lock only the selection, keep its data, and count repeat runs without changing it again.
        self.assertEqual(self.users.archive_users(), (1, 1))
        self.assertEqual(self.users.archive_users(), (0, 2))
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.admin_comments, "Keep these comments")
        self.assertFalse(self.other.user_locked)

    def test_archive_with_comments(self):
        # Add a year header once for newly archived users, preserving existing archived comments.
        with patch("intranet.apps.users.models.timezone.localdate", return_value=datetime.date(2026, 6, 20)):
            self.assertEqual(self.users.archive_users(update_admin_comments=True), (1, 1))
            self.assertEqual(self.users.archive_users(update_admin_comments=True), (0, 2))
        self.user.refresh_from_db()
        self.locked.refresh_from_db()
        self.assertEqual(self.user.admin_comments, "\n=== 2025-2026 comments ===\nKeep these comments")
        self.assertEqual(self.locked.admin_comments, "Already archived")

    def test_admin_action(self):
        # Exercise the registered action and both its success and already-archived messages.
        model_admin = admin.site._registry[get_user_model()]
        request = RequestFactory().post("/")
        with patch.object(model_admin, "message_user") as message_user:
            model_admin.archive_users(request, self.users)
        message_user.assert_any_call(request, "Archived 1 users.")
        message_user.assert_any_call(request, "1 users already archived.", level=messages.WARNING)
        self.user.refresh_from_db()
        self.assertTrue(self.user.user_locked)

    def test_csv_dry_run_and_run(self):
        # Deduplicate usernames, ignore empty cells, and report missing users without touching other accounts.
        contents = "\ufeffusername\n archive_me \nalready_locked\narchive_me\nmissing_user\n   \n"
        output = self.run_command(contents)
        self.assertIn("Identifiers provided: 4", output)
        self.assertIn("Unique identifiers: 3", output)
        self.assertIn("Duplicate identifiers: 1", output)
        self.assertIn("Matched users: 2", output)
        self.assertIn("Missing identifiers: 1", output)
        self.assertIn("Dry run mode.", output)
        self.user.refresh_from_db()
        self.assertFalse(self.user.user_locked)

        output = self.run_command(contents, "--run", "--confirm")
        self.assertIn("Archived users: 1", output)
        self.assertIn("Already archived users: 1", output)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertTrue(self.user.user_locked)
        self.assertFalse(self.other.user_locked)

    def test_csv_requires_username_header(self):
        # A malformed or empty file should produce an actionable error instead of silently doing nothing.
        for contents in ("", "student_id\n12345\n", "usernames\narchive_me\n"):
            with self.subTest(contents=contents), self.assertRaisesRegex(CommandError, "username"):
                self.run_command(contents, "--run", "--confirm")

    def test_empty_selection(self):
        self.assertIn("No identifiers found", self.run_command("username\n   \n"))

    def test_csv_confirmation_can_abort(self):
        # Declining the confirmation must leave the selected user active.
        with patch("builtins.input", return_value="n"):
            self.assertIn("Aborted.", self.run_command("username\narchive_me\n", "--run"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.user_locked)

    def test_unreadable_csv(self):
        with patch("intranet.apps.users.management.commands.archive_users.open", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(CommandError, "File not found"):
                call_command("archive_users", "--filename", "missing.csv")

    def test_archiving_blocks_existing_session(self):
        # An account archived after login must lose access on its next request.
        self.login(self.user.username)
        self.assertEqual(self.client.get(reverse("user_profile")).status_code, 200)
        self.users.archive_users()
        self.assertEqual(self.client.get(reverse("user_profile")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class CourseTest(IonTestCase):
    def setUp(self):
        self.create_schedule_test()

    def create_schedule_test(self):
        for i in range(9):
            course = Course.objects.create(name=f"Test Course {i}", course_id=f"1111{i}")
            for pd in range(1, 8):
                Section.objects.create(course=course, room=f"Room {i}", period=pd, section_id=f"{course.course_id}-{pd}", sem="F")

    def test_section_course_attributes(self):
        course = Course.objects.first()
        self.assertEqual(str(course), f"{course.name} ({course.course_id})")

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

        self.assertQuerySetEqual(get_user_model().objects.get_teachers(), list(map(repr, users)), transform=repr, ordered=False)

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
        self.assertEqual(user.tj_email, f"{user.username}@tjhsst.edu")
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
        self.assertEqual(user.tj_email, f"{user.username}@tjhsst.edu")
        self.assertEqual(user.non_tj_email, None)

        personal_email = Email.objects.create(user=user, address="abc@example.com")
        self.assertEqual(user.tj_email, f"{user.username}@tjhsst.edu")
        self.assertEqual(user.non_tj_email, personal_email.address)

        user.user_type = "teacher"
        user.save()
        self.assertEqual(user.tj_email, f"{user.username}@fcps.edu")
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

        user.gender = ""
        self.assertFalse(user.is_male)
        self.assertFalse(user.is_female)
        self.assertFalse(user.is_nonbinary)

        user.gender = "male"
        self.assertTrue(user.is_male)
        self.assertFalse(user.is_female)
        self.assertFalse(user.is_nonbinary)

        user.gender = "female"
        self.assertFalse(user.is_male)
        self.assertTrue(user.is_female)
        self.assertFalse(user.is_nonbinary)

        user.gender = "non-binary"
        self.assertFalse(user.is_male)
        self.assertFalse(user.is_female)
        self.assertTrue(user.is_nonbinary)


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
        self.auth = f"Bearer {tok.token}"  # pylint: disable=attribute-defined-outside-init

    def test_archiving_blocks_existing_oauth_token(self):
        # A token issued before archival must stop granting API access while the user is locked.
        self.make_admin()
        self.make_token()
        self.client.logout()
        url = reverse("api_user_myprofile_detail")
        self.assertEqual(self.client.get(url, HTTP_AUTHORIZATION=self.auth).status_code, 200)
        get_user_model().objects.filter(pk=self.user.pk).archive_users()
        self.assertIn(self.client.get(url, HTTP_AUTHORIZATION=self.auth).status_code, (401, 403))

    def test_client_credentials_token_without_user(self):
        # The account-lock check must preserve valid application tokens that have no associated user.
        token = AccessToken.objects.create(
            token="application_token",
            application=self.client_credentials_application,
            scope="read",
            expires=timezone.now() + datetime.timedelta(days=1),
        )
        request = SimpleNamespace()
        self.assertTrue(IonOIDCValidator().validate_bearer_token(token.token, ["read"], request))
        self.assertIsNone(request.user)

    def test_get_profile_api(self):
        self.make_admin()
        self.make_token()

        # Check for non-existent user.
        response = self.client.get(reverse("api_user_profile_detail", args=[9999]), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 404)

        # Get data for ourself.
        response = self.client.get(reverse("api_user_myprofile_detail"), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, 200)

        # Verify that response is the same
        response_with_username = self.client.get(
            reverse("api_user_myprofile_detail") + f"?username={self.user.username}", HTTP_AUTHORIZATION=self.auth
        )
        self.assertEqual(response_with_username.json(), response.json())
        response_with_pk = self.client.get(reverse("api_user_myprofile_detail") + f"?pk={self.user.pk}", HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response_with_pk.json(), response.json())

    def test_get_profile_picture_api(self):
        user = self.login()
        self.make_token()

        # Test with no pictures attached on default
        response = self.client.get(reverse("api_user_profile_picture_default", args=[user.pk]), HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.content_type, "image/jpeg")
        image_path = os.path.join(settings.PROJECT_ROOT, "static/img/default_profile_pic.png")
        with open(image_path, mode="rb") as f:
            self.assertEqual(response.content, f.read())
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

    def test_subschools_view(self) -> None:
        """Addresses come from each username's account, or from an address given outright."""
        self.login()

        subschools = [
            {
                "name": "Subschool 1",
                "administrator": {"name": "Mr. Explicit", "username": "sexplicit"},
                "administrative_assistant": {"name": "Ms. NoAccount", "email": "no.account@fcps.edu"},
                "counselors": [
                    {"name": "Ms. Guessed", "username": "sguessed"},
                    {"name": "Dr. Nobody", "username": "snobody"},
                ],
            }
        ]

        explicit = get_user_model().objects.get_or_create(username="sexplicit", user_type="teacher")[0]
        Email.objects.get_or_create(user=explicit, address="chosen.address@fcps.edu")
        get_user_model().objects.get_or_create(username="sguessed", user_type="counselor")
        # "snobody" deliberately has no account, and Ms. NoAccount has no username at all

        with self.settings(SUBSCHOOLS=subschools):
            response = self.client.get(reverse("subschools"))

        self.assertEqual(200, response.status_code)
        content = response.content.decode()

        # An address on the account wins over the guessed one
        self.assertIn("mailto:chosen.address@fcps.edu", content)
        # Otherwise tj_email guesses from the username
        self.assertIn("mailto:sguessed@fcps.edu", content)
        # An address configured outright is used as-is, for staff with no Ion account
        self.assertIn("mailto:no.account@fcps.edu", content)
        # A username with no account is named but not linked
        self.assertIn("Dr. Nobody", content)
        self.assertNotIn("mailto:snobody", content)

        # Settings are not mutated by the lookup
        self.assertNotIn("email", subschools[0]["administrator"])

    def test_subschools_view_username_must_match_exactly(self) -> None:
        """A username whose case differs from the account is not matched, and is logged."""
        self.login()

        subschools = [
            {
                "name": "Subschool 1",
                "administrator": {"name": "Ms. Exact", "username": "SExact1"},
                "administrative_assistant": {"name": "Mr. Wrongcase", "username": "SWrongcase1"},
                "counselors": [],
            }
        ]

        exact = get_user_model().objects.get_or_create(username="SExact1", user_type="teacher")[0]
        Email.objects.get_or_create(user=exact, address="exact.spelling@fcps.edu")
        # Stored lowercase while settings uses mixed case, so it must not resolve
        get_user_model().objects.get_or_create(username="swrongcase1", user_type="teacher")

        with self.settings(SUBSCHOOLS=subschools):
            with self.assertLogs("intranet.apps.users.views", level="WARNING") as logs:
                response = self.client.get(reverse("subschools"))

        content = response.content.decode()
        self.assertIn("mailto:exact.spelling@fcps.edu", content)
        self.assertNotIn("mailto:swrongcase1", content)
        self.assertIn("Mr. Wrongcase", content)
        self.assertTrue(any("SWrongcase1" in line for line in logs.output))

    def test_subschools_view_last_updated(self) -> None:
        """The configured last updated date is shown at the bottom of the page."""
        self.login()

        with self.settings(SUBSCHOOLS_LAST_UPDATED=datetime.date(1999, 3, 4)):
            response = self.client.get(reverse("subschools"))

        self.assertContains(response, "Last updated March 4, 1999.")

        with self.settings(SUBSCHOOLS_LAST_UPDATED=None):
            response = self.client.get(reverse("subschools"))

        self.assertNotContains(response, "Last updated")

    def test_subschools_view_requires_login(self) -> None:
        response = self.client.get(reverse("subschools"))
        self.assertEqual(302, response.status_code)
        self.assertIn("/login", response["Location"])

    def test_profile_view_administrator_row(self) -> None:
        """The Administrator row always shows for staff viewers, blank when the user has none."""
        admin_user = self.make_admin()
        administrator = get_user_model().objects.get_or_create(username="anadmin", last_name="Dawson", user_type="teacher")[0]
        counselor = get_user_model().objects.get_or_create(
            username="acounselor", last_name="Kim", user_type="counselor", administrator=administrator
        )[0]

        # A student with a counselor who has an administrator, but no administrator of their own
        student = get_user_model().objects.get_or_create(username="2021astudent", user_type="student", counselor=counselor)[0]

        response = self.client.get(reverse("user_profile", kwargs={"user_id": student.id}))
        self.assertEqual(200, response.status_code)
        # The row is present even though the field is unset...
        self.assertContains(response, "<th>Administrator</th>")
        # ...and it must not fall back to the counselor's administrator
        self.assertNotContains(response, administrator.last_name)

        # Once assigned, the student's own administrator shows
        student.administrator = administrator
        student.save(update_fields=["administrator"])
        response = self.client.get(reverse("user_profile", kwargs={"user_id": student.id}))
        self.assertContains(response, administrator.last_name)

        # The row also shows on a staff profile, where there is no counselor at all
        response = self.client.get(reverse("user_profile", kwargs={"user_id": admin_user.id}))
        self.assertContains(response, "<th>Administrator</th>")

    def test_privacy_options(self):
        self.assertEqual(set(PERMISSIONS_NAMES.keys()), {"self", "parent"})
        for k in ["self", "parent"]:
            self.assertEqual(set(PERMISSIONS_NAMES[k]), {"show_pictures", "show_address", "show_telephone", "show_eighth", "show_schedule"})

        self.assertEqual(set(self.user.permissions.keys()), {"self", "parent"})
        for k in ["self", "parent"]:
            self.assertEqual(
                set(self.user.permissions[k].keys()),
                {"show_pictures", "show_address", "show_telephone", "show_eighth", "show_schedule"},
            )
