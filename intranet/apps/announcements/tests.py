from django.contrib.auth import get_user_model
from django.urls import reverse

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..users.models import Group


class AnnouncementTest(IonTestCase):
    """Tests for the announcements module."""

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username="awilliam", graduation_year=get_senior_graduation_year() + 1)[0]

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
