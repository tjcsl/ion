from django.urls import reverse

from intranet.apps.eighth.tests.eighth_test import EighthAbstractTest


class EighthAttendanceTestCase(EighthAbstractTest):
    """Test cases for ``views.routers``."""

    def test_eighth_redirect_view(self):
        """Tests :func:`~intranet.apps.eighth.views.routers.eighth_redirect_view`."""

        user = self.login()

        # Start with a student
        user.user_type = "student"
        user.save()

        response = self.client.get(reverse("eighth_redirect"))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "eighth/signup.html")

        # Make this user a teacher
        user.user_type = "teacher"
        user.save()

        response = self.client.get(reverse("eighth_redirect"))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "eighth/take_attendance.html")

        # Try a service user
        user.user_type = "service"
        user.save()

        response = self.client.get(reverse("eighth_redirect"))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")

        # Now make this user a non-student admin
        user.user_type = "teacher"
        user.save()
        self.make_admin()

        response = self.client.get(reverse("eighth_redirect"))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "eighth/admin/dashboard.html")
