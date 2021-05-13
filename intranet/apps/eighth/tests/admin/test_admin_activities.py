from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from intranet.apps.groups.models import Group

from ...models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSponsor
from ..eighth_test import EighthAbstractTest


class EighthAdminActivitiesTest(EighthAbstractTest):
    def test_add_activity_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.activities.add_activity_view`."""

        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_add_activity"))
        self.assertEqual(200, response.status_code)

        # Add an activity
        EighthActivity.objects.all().delete()
        response = self.client.post(reverse("eighth_admin_add_activity"), data={"name": "Test Activity 1"})
        self.assertEqual(302, response.status_code)  # to edit activity page
        self.assertEqual(1, EighthActivity.objects.filter(name="Test Activity 1").count())

    def test_edit_activity_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.activities.edit_activity_view`."""

        user = self.make_admin()

        # Add an activity
        EighthActivity.objects.all().delete()
        activity = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}))
        self.assertEqual(200, response.status_code)

        # Make a change
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
            },
        )
        self.assertEqual(302, response.status_code)  # back to the same page
        self.assertEqual(
            1,
            EighthActivity.objects.filter(
                id=activity.id, name="test activity 2", description="haha", default_capacity=7, sticky=True, wed_a=True, fri_b=True, restricted=True
            ).count(),
        )

        # Try adding a sponsor
        sponsor = EighthSponsor.objects.get_or_create(user=user, first_name="A", last_name="William")[0]

        # Because there are no previous scheduled occurrences of this activity, this should not show the
        # "keep sponsor history" page.
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
            },
        )
        self.assertEqual(302, response.status_code)  # back to the same page
        self.assertEqual(
            1,
            EighthActivity.objects.filter(
                id=activity.id,
                name="test activity 2",
                description="haha",
                default_capacity=7,
                sticky=True,
                wed_a=True,
                fri_b=True,
                restricted=True,
                sponsors=sponsor,
            ).count(),
        )

        # Add another sponsor and schedule a block
        user2 = get_user_model().objects.get_or_create(username="twilliam")[0]
        sponsor2 = EighthSponsor.objects.get_or_create(user=user2, first_name="T", last_name="William")[0]
        block = EighthBlock.objects.get_or_create(date=(timezone.localtime() - timezone.timedelta(days=2)).date(), block_letter="A")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Attempt to change the sponsor
        scheduled.sponsors.clear()
        scheduled.save()
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id, sponsor2.id],
            },
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, response.context["sched_acts_count"])
        self.assertEqual([sponsor], list(EighthActivity.objects.get(id=activity.id).sponsors.all()))

        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id, sponsor2.id],
                "change_sponsor_history": "no",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([sponsor, sponsor2], list(EighthActivity.objects.get(id=activity.id).sponsors.all()))
        self.assertEqual([sponsor, sponsor2], list(EighthScheduledActivity.objects.get(id=scheduled.id).get_true_sponsors()))

        # Try again but "no" this time
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "change_sponsor_history": "yes",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([sponsor], list(EighthActivity.objects.get(id=activity.id).sponsors.all()))
        self.assertEqual([sponsor, sponsor2], list(EighthScheduledActivity.objects.get(id=scheduled.id).get_true_sponsors()))

        # Now, try changing the room
        scheduled.rooms.clear()
        scheduled.save()
        room1 = EighthRoom.objects.get_or_create(name="test room 1", capacity=100)[0]
        room2 = EighthRoom.objects.get_or_create(name="test room 2", capacity=200)[0]

        activity.rooms.add(room1)
        activity.save()

        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "rooms": [room1.id, room2.id],
            },
        )
        self.assertEqual(200, response.status_code)  # rendering the "keep room history" page
        self.assertTemplateUsed(response, "eighth/admin/keep_room_history.html")

        # Say "yes" - i.e. have the extra room only apply for new activities
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "rooms": [room1.id, room2.id],
                "change_room_history": "yes",
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual([room1, room2], list(EighthActivity.objects.get(id=activity.id).rooms.all()))
        self.assertEqual([room1], list(EighthScheduledActivity.objects.get(id=scheduled.id).get_true_rooms()))

        # Now, follow the request to ensure that notification emails are sent
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "rooms": [room2.id],
                "change_room_history": "yes",
            },
            follow=True,
        )
        self.assertIn("Notifying students of this room change.", list(map(str, list(response.context["messages"]))))

        # Now, make sure room emails aren't sent if the room doesn't change by making sure nothing is logged
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "rooms": [room2.id],
                "change_room_history": "yes",
            },
            follow=True,
        )
        self.assertNotIn("Notifying students of this room change.", list(map(str, list(response.context["messages"]))))

        # Now, say "no" - i.e. have the change propagate
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "rooms": [room1.id],
                "change_room_history": "no",
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual([room1], list(EighthActivity.objects.get(id=activity.id).rooms.all()))
        self.assertEqual([room1], list(EighthScheduledActivity.objects.get(id=scheduled.id).get_true_rooms()))

        # Test "add a group" for creating a group for restricted lists
        response = self.client.post(
            reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}),
            data={
                "name": "test activity 2",
                "description": "haha",
                "default_capacity": 7,
                "sticky": "sticky",
                "wed_a": "on",
                "fri_b": "on",
                "restricted": "on",
                "sponsors": [sponsor.id],
                "rooms": [room1.id],
                "add_group": "add_group",
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            reverse("eighth_admin_edit_group", kwargs={"group_id": Group.objects.get(name="Activity: test activity 2").id}), response.url
        )
        self.assertTrue(EighthActivity.objects.get(id=activity.id).restricted)
        self.assertIn(Group.objects.get(name="Activity: test activity 2"), EighthActivity.objects.get(id=activity.id).groups_allowed.all())

        # Load the "edit" page again
        response = self.client.get(reverse("eighth_admin_edit_activity", kwargs={"activity_id": activity.id}))
        self.assertEqual(200, response.status_code)

    def test_delete_activity_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.activities.delete_activity_view`."""

        self.make_admin()

        # Add an activity then load the page
        EighthActivity.objects.all().delete()
        activity = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]

        response = self.client.get(reverse("eighth_admin_delete_activity", kwargs={"activity_id": activity.id}))
        self.assertEqual(200, response.status_code)

        # Now, delete it
        response = self.client.post(reverse("eighth_admin_delete_activity", kwargs={"activity_id": activity.id}))
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthActivity.objects.filter(id=activity.id, deleted=True).count())

        # Try permanent deletion
        response = self.client.get(reverse("eighth_admin_delete_activity", kwargs={"activity_id": activity.id}), data={"perm": "perm"})
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse("eighth_admin_delete_activity", kwargs={"activity_id": activity.id}) + "?perm")
        self.assertEqual(302, response.status_code)
        self.assertEqual(0, EighthActivity.objects.filter(id=activity.id).count())
