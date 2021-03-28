import csv

from django.urls import reverse
from django.utils import timezone

from ...models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity
from ..eighth_test import EighthAbstractTest


class EighthAdminRoomsTest(EighthAbstractTest):
    def test_add_room_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.rooms.add_room_view`"""
        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_add_room"))
        self.assertEqual(200, response.status_code)

        # Add an activity for testing
        activity = EighthActivity.objects.get_or_create(name="test activity")[0]

        response = self.client.post(
            reverse("eighth_admin_add_room"),
            {
                "name": "Room 3",
                "capacity": 1,
                "activities": [activity.id],
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthRoom.objects.filter(name="Room 3", capacity=1).count())
        self.assertIn(EighthRoom.objects.get(name="Room 3", capacity=1), EighthActivity.objects.get(id=activity.id).rooms.all())

    def test_edit_room_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.rooms.edit_room_view`"""
        self.make_admin()
        act1 = EighthActivity.objects.create(name="Act1")
        room1 = EighthRoom.objects.create(name="Room 1", capacity=1)
        room2 = EighthRoom.objects.create(name="Room 2", capacity=1)
        act1.rooms.add(room1)
        act1.save()

        # Load the page
        response = self.client.get(reverse("eighth_admin_edit_room", kwargs={"room_id": room2.id}))
        self.assertEqual(200, response.status_code)

        # Schedule act1 in room2
        response = self.client.post(
            reverse("eighth_admin_edit_room", args=[room2.id]),
            {
                "name": "Room 2",
                "capacity": 1,
                "activities": [act1.id],
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(2, len(EighthActivity.objects.get(id=act1.id).rooms.all()))

    def test_delete_room_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.rooms.delete_room_view`"""

        # Make us an admin and make a room
        self.make_admin()
        room1 = EighthRoom.objects.create(name="Room 1", capacity=1)

        # Load the page
        response = self.client.get(reverse("eighth_admin_delete_room", kwargs={"room_id": room1.id}))
        self.assertEqual(200, response.status_code)

        # Delete the room
        response = self.client.post(reverse("eighth_admin_delete_room", kwargs={"room_id": room1.id}))
        self.assertEqual(302, response.status_code)
        self.assertEqual(0, EighthRoom.objects.filter(id=room1.id).count())

    def test_room_sanity_check_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.rooms.room_sanity_check_view`"""

        # Make us an admin and a room
        self.make_admin()
        room1 = EighthRoom.objects.create(name="Room 1", capacity=1)

        # Make two activities: one scheduled to that room, one not
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        EighthScheduledActivity.objects.get_or_create(block=block, activity=activity1, capacity=5)
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]
        EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2, capacity=5)

        activity1.rooms.add(room1)
        activity1.save()

        # Load the page - should ask what block we want
        response = self.client.get(reverse("eighth_admin_room_sanity_check"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([block], list(response.context["blocks"]))
        self.assertIsNone(response.context["chosen_block"])

        # Load again and pick the first block
        response = self.client.get(reverse("eighth_admin_room_sanity_check"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([], response.context["room_conflicts"])  # No conflicts yet

        # Schedule activity2 for room1
        activity2.rooms.add(room1)
        activity2.save()

        # Load again, should have a conflict
        response = self.client.get(reverse("eighth_admin_room_sanity_check"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(block, response.context["chosen_block"])
        self.assertEqual([{"room_name": room1.name, "activities": [activity1, activity2]}], response.context["room_conflicts"])

    def test_room_utilization_for_block_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.rooms.room_utilization_for_block_view`"""

        # Make us an admin
        self.make_admin()

        # Make a block and an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        EighthScheduledActivity.objects.get_or_create(block=block, activity=activity1, capacity=5)

        # Load the page
        response = self.client.get(reverse("eighth_admin_room_utilization_for_block"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([block], list(response.context["blocks"]))

        # GET the block
        response = self.client.get(reverse("eighth_admin_room_utilization_for_block"), data={"block": block.id})
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_admin_room_utilization", kwargs={"start_id": block.id, "end_id": block.id}), response.url)

        # The room utilization view is tested later

    def test_room_utilization_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.rooms.room_utilization_view` - the wizard only"""

        # Make us an admin
        self.make_admin()

        # Make us two blocks
        today = timezone.localtime().date()
        block1 = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        block2 = EighthBlock.objects.get_or_create(date=today, block_letter="B")[0]

        # Load the first page
        response = self.client.get(reverse("eighth_admin_room_utilization"))
        self.assertEqual(200, response.status_code)

        # POST to the second page
        response = self.client.post(
            reverse("eighth_admin_room_utilization"),
            data={"eighth_admin_room_utilization_wizard-current_step": "start_block", "start_block-block": block1.id},
        )
        self.assertEqual(200, response.status_code)

        # POST to the third page (i.e. select the end block)
        response = self.client.post(
            reverse("eighth_admin_room_utilization"),
            data={"eighth_admin_room_utilization_wizard-current_step": "end_block", "end_block-block": block2.id},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_admin_room_utilization", kwargs={"start_id": block1.id, "end_id": block2.id}), response.url)

        # The room utilization view is tested later

    def test_eighth_room_utilization(self):
        """Ensure that the room utilization check filters properly."""
        self.make_admin()

        EighthRoom.objects.all().delete()

        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)
        act1 = self.add_activity(name="Test Activity 1", room=room1)
        schact1 = EighthScheduledActivity.objects.create(block=block1, activity=act1)
        schact1.rooms.add(room1)
        schact1.save()

        response = self.client.get(reverse("eighth_admin_room_utilization", args=[block1.id, block1.id]))
        self.assertEqual(200, response.status_code)

        # Test filtering for room1
        response = self.client.get(reverse("eighth_admin_room_utilization", args=[block1.id, block1.id]), {"room": room1.id})
        self.assertEqual(list(response.context["scheduled_activities"]), [schact1])
        self.assertEqual(200, response.status_code)

        # Test CSV output
        response = self.client.get(reverse("eighth_admin_room_utilization_csv", args=[block1.id, block1.id]), {"room": room1.id, "show_used": True})
        self.assertEqual(200, response.status_code)
        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
