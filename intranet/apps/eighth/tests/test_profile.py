from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ....utils.date import get_senior_graduation_year
from ...users.models import Grade
from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from .eighth_test import EighthAbstractTest


class EighthProfileTest(EighthAbstractTest):
    def test_profile_view(self):
        """Tests :func:`~intranet.apps.eighth.views.profile.profile_view`."""
        EighthBlock.objects.all().delete()
        get_user_model().objects.all().delete()

        # First, log in and show this user's own eighth profile page
        user2 = get_user_model().objects.get_or_create(username="2021awilliam", user_type="student")[0]
        user = get_user_model().objects.get_or_create(username="awilliam", user_type="teacher")[0]
        self.login("2021awilliam")
        response = self.client.get(reverse("eighth_profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user2, response.context["profile_user"])
        self.assertEqual([], response.context["eighth_schedule"])

        # Now, try to load some other page
        response = self.client.get(reverse("eighth_profile", kwargs={"user_id": user.id}))
        self.assertEqual(403, response.status_code)

        # Add a block and an eighth period activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A", locked=True)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        response = self.client.get(reverse("eighth_profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user2, response.context["profile_user"])
        self.assertEqual([{"block": block, "signup": None}], response.context["eighth_schedule"])

        # Now, sign the student up for that activity
        signup = EighthSignup.objects.create(scheduled_activity=scheduled, user=user2)

        response = self.client.get(reverse("eighth_profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user2, response.context["profile_user"])
        self.assertEqual([{"block": block, "signup": signup}], response.context["eighth_schedule"])

        # Now, try as an eighth period sponsor
        user = self.make_admin()
        sponsor = EighthSponsor.objects.get_or_create(first_name="a", last_name="william", user=user)[0]
        scheduled.sponsors.add(sponsor)
        scheduled.save()

        response = self.client.get(reverse("eighth_profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["profile_user"])
        self.assertEqual([scheduled], list(response.context["eighth_sponsor_schedule"]))

    def test_profile_history_view(self):
        """Tests :func:`~intranet.apps.eighth.views.profile.profile_history_view`."""
        get_user_model().objects.all().delete()

        # Log in and load the page
        user = self.login()
        response = self.client.get(reverse("eighth_profile_history"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["profile_user"])
        self.assertFalse(response.context["show_profile_header"])

        # Make sure that I can't load someone else's page
        user2 = get_user_model().objects.get_or_create(username="2021awilliam", user_type="student")[0]
        response = self.client.get(reverse("eighth_profile_history", kwargs={"user_id": user2.id}))
        self.assertEqual(403, response.status_code)

        # Add an EighthBlock and an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A", locked=True)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        response = self.client.get(reverse("eighth_profile_history"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([{"block": block, "signup": None}], response.context["eighth_schedule"])

        # Add a signup
        signup = EighthSignup.objects.get_or_create(
            user=user,
            scheduled_activity=scheduled,
        )[0]

        response = self.client.get(reverse("eighth_profile_history"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([{"block": block, "signup": signup, "highlighted": False}], response.context["eighth_schedule"])

    def test_profile_often_view(self):
        """Tests :func:`~intranet.apps.eighth.views.profile.profile_often_view`."""
        get_user_model().objects.all().delete()

        # Log in and load the page
        user = self.login()
        response = self.client.get(reverse("eighth_profile_often"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["profile_user"])
        self.assertFalse(response.context["show_profile_header"])

        # Make sure that I can't load someone else's page
        user2 = get_user_model().objects.get_or_create(username="2021awilliam", user_type="student")[0]
        response = self.client.get(reverse("eighth_profile_often", kwargs={"user_id": user2.id}))
        self.assertEqual(403, response.status_code)

        # Add an EighthBlock and an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A", locked=True)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        response = self.client.get(reverse("eighth_profile_often"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.context["oftens"])

        # Add a signup
        EighthSignup.objects.get_or_create(user=user, scheduled_activity=scheduled)

        response = self.client.get(reverse("eighth_profile_often"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([{"count": 1, "activity": activity}], response.context["oftens"])

    def test_profile_signup_view(self):
        """Tests :func:`~intranet.apps.eighth.views.profile.profile_signup_view`."""

        get_user_model().objects.all().delete()
        EighthBlock.objects.all().delete()

        # Add a block and an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Log in and load the page
        user = self.login()
        response = self.client.get(reverse("eighth_profile_signup", kwargs={"user_id": user.id, "block_id": block.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["user"])
        self.assertEqual(block, response.context["active_block"])
        self.assertIsNone(response.context["active_block_current_signup"])

        # Add a signup
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled)

        response = self.client.get(reverse("eighth_profile_signup", kwargs={"user_id": user.id, "block_id": block.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["user"])
        self.assertEqual(block, response.context["active_block"])
        self.assertEqual(scheduled.id, response.context["active_block_current_signup"])

        # Assert that I cannot load someone else's page
        user2 = get_user_model().objects.get_or_create(username="2021awilliam", user_type="student")[0]
        response = self.client.get(reverse("eighth_profile_signup", kwargs={"user_id": user2.id, "block_id": block.id}))
        self.assertEqual(403, response.status_code)

        # Make me an admin then try again
        self.make_admin()
        response = self.client.get(reverse("eighth_profile_signup", kwargs={"user_id": user2.id, "block_id": block.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user2, response.context["user"])
        self.assertEqual(block, response.context["active_block"])
        self.assertIsNone(response.context["active_block_current_signup"])

    def test_edit_profile_view(self):
        """Tests :func:`~intranet.apps.eighth.views.profile.edit_profile_view`."""

        get_user_model().objects.all().delete()

        self.make_admin()
        user2 = get_user_model().objects.get_or_create(username="2021awilliam", user_type="student")[0]

        # Load the page.
        response = self.client.get(reverse("eighth_edit_profile", kwargs={"user_id": user2.id}))
        self.assertEqual(200, response.status_code)

        # Change something
        response = self.client.post(
            reverse("eighth_edit_profile", kwargs={"user_id": user2.id}),
            data={
                "admin_comments": "===2020-2021===\nNone",
                "student_id": 1234678,
                "first_name": "Angela",
                "last_name": "William",
                "middle_name": "Hello",
                "nickname": "A",
                "graduation_year": get_senior_graduation_year(),
                "gender": False,
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        user2 = get_user_model().objects.get(id=user2.id)
        self.assertEqual("===2020-2021===\nNone", user2.admin_comments)
        self.assertEqual("1234678", user2.student_id)
        self.assertEqual("Angela", user2.first_name)
        self.assertEqual("William", user2.last_name)
        self.assertEqual("Hello", user2.middle_name)
        self.assertEqual("A", user2.nickname)
        self.assertEqual(get_senior_graduation_year(), Grade.year_from_grade(user2.grade.number))
        self.assertFalse(user2.gender)
