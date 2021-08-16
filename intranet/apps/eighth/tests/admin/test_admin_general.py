import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from intranet.apps.groups.models import Group

from .....utils.helpers import awaredate
from ...models import EighthActivity, EighthBlock, EighthRoom, EighthSponsor
from ..eighth_test import EighthAbstractTest


class EighthAdminGeneralTest(EighthAbstractTest):
    def test_eighth_admin_dashboard_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.general.eighth_admin_dashboard_view`."""

        user = self.login()
        # Test as non-eighth admin
        response = self.client.get(reverse("eighth_admin_dashboard"))
        self.assertEqual(response.status_code, 302)

        user = self.make_admin()

        for i in range(1, 21):
            self.add_activity(name="Test{}".format(i))
            Group.objects.create(name="Test{}".format(i))
            user = get_user_model().objects.create(username="awilliam{}".format(i))
            EighthRoom.objects.create(name="Test{}".format(i))
            EighthSponsor.objects.create(user=user, first_name="Angela{}".format(i), last_name="William")

        self.add_block(date="9001-4-20", block_letter="A")

        response = self.client.get(reverse("eighth_admin_dashboard"))
        self.assertTemplateUsed(response, "eighth/admin/dashboard.html")

        self.assertEqual(response.context["start_date"], awaredate())
        self.assertQuerysetEqual(
            response.context["all_activities"], [repr(activity) for activity in EighthActivity.objects.all().order_by("name")], transform=repr
        )
        self.assertQuerysetEqual(response.context["blocks_after_start_date"], [repr(block) for block in EighthBlock.objects.all()], transform=repr)
        self.assertQuerysetEqual(response.context["groups"], [repr(group) for group in Group.objects.all().order_by("name")], transform=repr)
        self.assertQuerysetEqual(response.context["rooms"], [repr(room) for room in EighthRoom.objects.all()], transform=repr)
        self.assertQuerysetEqual(
            response.context["sponsors"],
            [repr(sponsor) for sponsor in EighthSponsor.objects.order_by("last_name", "first_name").all()],
            transform=repr,
        )
        self.assertQuerysetEqual(
            response.context["blocks_next"], [repr(block) for block in EighthBlock.objects.filter(date="9001-4-20").all()], transform=repr
        )
        self.assertEqual(response.context["blocks_next_date"], datetime.datetime(9001, 4, 20).date())
        self.assertEqual(response.context["admin_page_title"], "Eighth Period Admin")
        self.assertEqual(response.context["signup_users_count"], get_user_model().objects.get_students().count())

    def test_edit_start_date_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.general.edit_start_date_view`."""

        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_edit_start_date"))
        self.assertEqual(200, response.status_code)

        # Change the date - set it to yesterday
        response = self.client.post(
            reverse("eighth_admin_edit_start_date"), data={"date": (timezone.localtime().date() - timezone.timedelta(days=1)).isoformat()}
        )
        self.assertEqual(302, response.status_code)

    def test_cache_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.general.cache_view`."""

        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_cache"))
        self.assertEqual(200, response.status_code)

        # Change the date - set it to yesterday
        response = self.client.post(reverse("eighth_admin_cache"), data={"invalidate_all": True})
        self.assertEqual(200, response.status_code)

    def test_history_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.general.history_view`."""

        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_history"))
        self.assertEqual(200, response.status_code)
