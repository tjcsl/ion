import csv

from django.urls import reverse
from django.utils import timezone

from ...models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSponsor
from ..eighth_test import EighthAbstractTest


class EighthAdminSponsorsTest(EighthAbstractTest):
    def test_add_sponsor_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.sponsors.add_sponsor_view`."""
        # Make sure user not in database is not created
        self.make_admin()
        params = {
            "first_name": "Test",
            "last_name": "User",
            "user": 9001,
            "department": "general",
            "online_attendance": "on",
            "contracted_eighth": "on",
        }

        # Load the page
        response = self.client.get(reverse("eighth_admin_add_sponsor"))
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse("eighth_admin_add_sponsor"), params, follow=True)
        self.assertEqual(response.status_code, 200)

        # Test that error is raised and redirects
        self.assertTemplateUsed(response, "eighth/admin/add_sponsor.html")

        self.assertFormError(response, "form", "user", "Select a valid choice. {} is not one of the available choices.".format(params["user"]))

        user = self.create_sponsor()
        params = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user": user.pk,
            "department": "general",
            "online_attendance": "on",
            "full_time": "on",
        }

        response = self.client.post(reverse("eighth_admin_add_sponsor"), params, follow=True)
        self.assertEqual(response.status_code, 200)

        # Make sure that new EighthSponsor is created
        self.assertTrue(EighthSponsor.objects.filter(user=user).exists())

    def test_list_sponsor_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.sponsors.list_sponsor_view`."""

        user = self.make_admin()

        # Load the page.
        response = self.client.get(reverse("eighth_admin_list_sponsor"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], list(response.context["blocks"]))

        # Add a block
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]

        response = self.client.get(reverse("eighth_admin_list_sponsor"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([block], list(response.context["blocks"]))

        response = self.client.get(reverse("eighth_admin_list_sponsor"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual([block], list(response.context["blocks"]))
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([], response.context["sponsor_list"])

        # Add an activity with a sponsor
        sponsor = EighthSponsor.objects.get_or_create(first_name="A", last_name="William", user=user)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        activity.sponsors.add(sponsor)
        activity.save()

        # Load the page
        response = self.client.get(reverse("eighth_admin_list_sponsor"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual([block], list(response.context["blocks"]))
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([(sponsor, [scheduled])], response.context["sponsor_list"])

        # Get a CSV
        response = self.client.get(reverse("eighth_admin_list_sponsor_csv"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual("William", reader_contents[0]["Sponsor"])
        self.assertEqual("Test Activity", reader_contents[0]["Activity"])

    def test_edit_sponsor_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.sponsors.edit_sponsor_view`."""

        user = self.make_admin()

        # Add a sponsor
        sponsor = EighthSponsor.objects.get_or_create(first_name="A", last_name="William", user=user)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_edit_sponsor", kwargs={"sponsor_id": sponsor.id}))
        self.assertEqual(200, response.status_code)

        # Change the name
        response = self.client.post(
            reverse("eighth_admin_edit_sponsor", kwargs={"sponsor_id": sponsor.id}),
            data={
                "first_name": "Alice",
                "last_name": "William",
                "department": "general",
                "full_time": "on",
                "contracted_eighth": "on",
                "user": user.id,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            1,
            EighthSponsor.objects.filter(
                first_name="Alice",
                last_name="William",
                user=user,
                department="general",
                full_time=True,
                contracted_eighth=True,
                online_attendance=False,
            ).count(),
        )

    def test_delete_sponsor_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.sponsors.delete_sponsor_view`."""
        user = self.make_admin()

        # Add a sponsor
        sponsor = EighthSponsor.objects.get_or_create(first_name="A", last_name="William", user=user)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_delete_sponsor", kwargs={"sponsor_id": sponsor.id}))
        self.assertEqual(200, response.status_code)

        # Delete the sponsor
        response = self.client.post(reverse("eighth_admin_delete_sponsor", kwargs={"sponsor_id": sponsor.id}))
        self.assertEqual(302, response.status_code)

        self.assertEqual(0, EighthSponsor.objects.filter(id=sponsor.id).count())

    def test_sponsor_schedule_view(self):
        user = self.make_admin()

        # Add a sponsor
        sponsor = EighthSponsor.objects.get_or_create(first_name="A", last_name="William", user=user)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_sponsor_schedule", kwargs={"sponsor_id": sponsor.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], list(response.context["scheduled_activities"]))
        self.assertEqual([], list(response.context["activities"]))
        self.assertEqual(sponsor, response.context["sponsor"])

        # Add an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        activity.sponsors.add(sponsor)
        activity.save()

        response = self.client.get(reverse("eighth_admin_sponsor_schedule", kwargs={"sponsor_id": sponsor.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual([scheduled], list(response.context["scheduled_activities"]))

        # Add a second activity
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2)[0]
        activity2.sponsors.add(sponsor)
        activity2.save()

        response = self.client.get(reverse("eighth_admin_sponsor_schedule", kwargs={"sponsor_id": sponsor.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual([scheduled, scheduled2], list(response.context["scheduled_activities"]))

        # Filter by activity
        response = self.client.get(reverse("eighth_admin_sponsor_schedule", kwargs={"sponsor_id": sponsor.id}), data={"activity": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual([scheduled], list(response.context["scheduled_activities"]))

    def test_sponsor_sanity_check_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.sponsors.sponsor_sanity_check_view`."""

        user = self.make_admin()

        # Add a sponsor
        sponsor = EighthSponsor.objects.get_or_create(first_name="A", last_name="William", user=user)[0]

        # Add an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)
        activity.sponsors.add(sponsor)
        activity.save()

        # Load the page
        response = self.client.get(reverse("eighth_admin_sponsor_sanity_check"))
        self.assertEqual(200, response.status_code)
        self.assertIsNone(response.context["chosen_block"])
        self.assertEqual([block], list(response.context["blocks"]))

        # Select the block
        response = self.client.get(reverse("eighth_admin_sponsor_sanity_check"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([], response.context["sponsor_conflicts"])

        # Add a second activity
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]
        EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2)
        activity2.sponsors.add(sponsor)
        activity2.save()

        # Load again, a conflict should now appear
        response = self.client.get(reverse("eighth_admin_sponsor_sanity_check"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([{"sponsor_name": "William", "activities": [activity, activity2]}], response.context["sponsor_conflicts"])

        # Set activity2 to deleted
        activity2.deleted = True
        activity2.save()

        # No conflict
        response = self.client.get(reverse("eighth_admin_sponsor_sanity_check"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([], response.context["sponsor_conflicts"])
