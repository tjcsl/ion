from django.contrib.auth import get_user_model
from django.urls import reverse

from ..eighth_test import EighthAbstractTest


class EighthAdminUsersTest(EighthAbstractTest):
    def test_list_user_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.users.list_user_view`."""

        get_user_model().objects.all().delete()
        user = self.make_admin()

        response = self.client.get(reverse("eighth_admin_manage_users"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([user], list(response.context["users"]))

    def test_delete_user_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.users.delete_user_view`."""
        user = self.make_admin()

        # Try to delete ourselves (or, rather, load the page to delete ourself)
        response = self.client.get(reverse("eighth_admin_manage_users"), args=user.id)
        self.assertEqual(200, response.status_code)
