from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ...models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..eighth_test import EighthAbstractTest


class EighthAdminBlocksTest(EighthAbstractTest):
    def test_add_block_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.blocks.add_block_view`."""

        self.make_admin()

        # Load the page.
        response = self.client.get(reverse("eighth_admin_add_block"))
        self.assertEqual(200, response.status_code)

        # The first step (to show the rest of the page) is to select a date, so we'll do that here
        response = self.client.get(reverse("eighth_admin_add_block"), data={"date": timezone.localtime().date().isoformat()})
        self.assertEqual(200, response.status_code)

        # Add an A block
        response = self.client.post(
            reverse("eighth_admin_add_block"), data={"date": timezone.localtime().date().isoformat(), "modify_blocks": True, "blocks": ["A"]}
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, EighthBlock.objects.filter(date=timezone.localtime().date().isoformat(), block_letter="A").count())

        # Remove the A block
        response = self.client.post(
            reverse("eighth_admin_add_block"), data={"date": timezone.localtime().date().isoformat(), "modify_blocks": True, "blocks": []}
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, EighthBlock.objects.filter(date=timezone.localtime().date().isoformat(), block_letter="A").count())

    def test_edit_block_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.blocks.edit_block_view`."""

        self.make_admin()

        # Make a block
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]

        # Load the edit page
        response = self.client.get(reverse("eighth_admin_edit_block", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)

        # Edit the block (lock it)
        response = self.client.post(
            reverse("eighth_admin_edit_block", kwargs={"block_id": block.id}),
            data={"date": today.isoformat(), "block_letter": "A", "locked": True, "signup_time": "12:40:00", "comments": "hi"},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthBlock.objects.filter(date=today, block_letter="A", locked=True, comments="hi", signup_time="12:40:00").count())

    def test_copy_block_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.blocks.copy_block_view`."""

        self.make_admin()

        # Add a block with an activity scheduled
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Add B block
        block2 = EighthBlock.objects.get_or_create(date=today, block_letter="B")[0]

        # Load the "copy" page
        response = self.client.get(reverse("eighth_admin_copy_block", kwargs={"block_id": block2.id}))
        self.assertEqual(200, response.status_code)

        # Copy from A block only the activities
        response = self.client.post(reverse("eighth_admin_copy_block", kwargs={"block_id": block2.id}), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.context["new_activities"])
        self.assertEqual(0, response.context["new_signups"])
        self.assertEqual(1, EighthScheduledActivity.objects.filter(block=block2, activity=activity).count())

        # Create a user with a signup on A block
        user = get_user_model().objects.get_or_create(username="2021ttest", first_name="T", last_name="Test")[0]
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled)

        # Copy again but this time do signups too
        # There should be no duplicate EighthScheduledActivity
        response = self.client.post(reverse("eighth_admin_copy_block", kwargs={"block_id": block2.id}), data={"block": block.id, "signups": True})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.context["new_activities"])
        self.assertEqual(1, response.context["new_signups"])
        self.assertEqual(1, EighthScheduledActivity.objects.filter(block=block2, activity=activity).count())
        self.assertEqual(1, EighthSignup.objects.filter(scheduled_activity__block=block2, user=user).count())

    def test_delete_block_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.blocks.delete_block_view`."""

        self.make_admin()

        # Add a block
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_delete_block", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)

        # Delete the block
        response = self.client.post(reverse("eighth_admin_delete_block", kwargs={"block_id": block.id}))
        self.assertEqual(302, response.status_code)
        self.assertEqual(0, EighthBlock.objects.filter(id=block.id).count())

    def test_print_block_rosters_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.blocks.print_block_rosters_view`."""

        self.make_admin()

        # Start by loading the page with a block
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        response = self.client.get(reverse("eighth_admin_print_block_rosters", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(block, response.context["eighthblock"])
        self.assertEqual([scheduled], list(response.context["schacts"]))

        # Print a roster - I mean I can't parse a PDF to see if it's valid, though...
        response = self.client.post(reverse("eighth_admin_print_block_rosters", kwargs={"block_id": block.id}), data={"schact_id": scheduled.id})
        self.assertEqual(200, response.status_code)
