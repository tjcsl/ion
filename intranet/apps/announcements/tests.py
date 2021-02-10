from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..users.models import Group
from .models import AnnouncementRequest


class AnnouncementTest(IonTestCase):

    """Tests for the announcements module."""

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(
            username="awilliam", graduation_year=get_senior_graduation_year() + 1, user_type="student"
        )[0]

    def test_get_announcements(self):
        self.login()
        response = self.client.get(reverse("view_announcements"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("view_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_change_announcements(self):
        self.login()
        group = Group.objects.get_or_create(name="admin_all")[0]
        get_user_model().objects.get_or_create(username="awilliam")[0].groups.add(group)

        response = self.client.get(reverse("add_announcement"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin_approve_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("approve_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("announcements_archive"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("delete_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("hide_announcement"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("modify_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("request_announcement"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("show_announcement"))
        self.assertEqual(response.status_code, 404)

    def test_announcement_approval_allowed_users(self):
        """Tests to ensure that only allowed users can approve announcements."""
        teacher = get_user_model().objects.get_or_create(username="teacher", user_type="teacher", first_name="timmy", last_name="teacher")[0]
        counselor = get_user_model().objects.get_or_create(username="counselor", user_type="counselor", first_name="c", last_name="c")[0]
        user = get_user_model().objects.get_or_create(username="user", user_type="user", first_name="ursula", last_name="user")[0]
        student = get_user_model().objects.get_or_create(username="3000student", user_type="student", first_name="s", last_name="tudent")[0]
        self.assertEqual(list(get_user_model().objects.get_approve_announcements_users_sorted()), [counselor, teacher, user])
        self.assertNotIn(student, get_user_model().objects.get_approve_announcements_users_sorted())

    def test_announcement_request(self):
        """Tests the announcement request view."""
        self.login()
        response = self.client.get(reverse("request_announcement"))
        self.assertEqual(response.status_code, 200)

        teacher = get_user_model().objects.get_or_create(username="awilliam1", user_type="teacher", first_name="a", last_name="william")[0]

        # Now, try to POST an announcement
        response = self.client.post(
            reverse("request_announcement"),
            data={
                "title": "This is a test!",
                "author": "Sysadmins",
                "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "expiration_date": "3000-01-01 00:00:00",
                "teachers_requested": str(teacher.id),
                "notes": "Enter something here!",
            },
        )

        self.assertEqual(response.status_code, 302)  # to "success" page

        self.assertEqual(1, AnnouncementRequest.objects.count())

        # See if that AnnouncementRequest appears
        self.assertEqual(
            AnnouncementRequest.objects.filter(
                title="This is a test!",
                author="Sysadmins",
                content="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                teachers_requested=teacher,
                notes="Enter something here!",
            ).count(),
            1,
        )
