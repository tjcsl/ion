from django.urls import reverse

from ..eighth_test import EighthAbstractTest


class EighthAdminMaintenanceTest(EighthAbstractTest):
    def test_index_view(self):
        self.make_admin()
        self.reauth()

        response = self.client.get(reverse("eighth_admin_maintenance"))
        self.assertEqual(200, response.status_code)

    def test_start_of_year_view(self):
        self.make_admin()
        self.reauth()

        response = self.client.get(reverse("eighth_admin_maintenance_start_of_year"))
        self.assertEqual(200, response.status_code)

    def test_clear_comments_view(self):
        self.make_admin()
        self.reauth()

        response = self.client.get(reverse("eighth_admin_maintenance_clear_comments"))
        self.assertEqual(200, response.status_code)
