import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ....utils.date import get_senior_graduation_year
from ...groups.models import Group
from ...schedule.models import Block, Day, DayType, Time
from ..models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor
from .test_general import EighthAbstractTest


class EighthAdminTest(EighthAbstractTest):
    def add_activity(self, **args):
        response = self.client.post(reverse("eighth_admin_add_activity"), args)
        self.assertEqual(response.status_code, 302)
        return EighthActivity.objects.get(name=args["name"])

    def test_eighth_admin_dashboard_view(self):
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

        self.assertEqual(response.context["start_date"], timezone.localdate())
        self.assertQuerysetEqual(response.context["all_activities"], [repr(activity) for activity in EighthActivity.objects.all().order_by("name")])
        self.assertQuerysetEqual(response.context["blocks_after_start_date"], [repr(block) for block in EighthBlock.objects.all()])
        self.assertQuerysetEqual(response.context["groups"], [repr(group) for group in Group.objects.all().order_by("name")])
        self.assertQuerysetEqual(response.context["rooms"], [repr(room) for room in EighthRoom.objects.all()])
        self.assertQuerysetEqual(
            response.context["sponsors"], [repr(sponsor) for sponsor in EighthSponsor.objects.order_by("last_name", "first_name").all()]
        )
        self.assertQuerysetEqual(response.context["blocks_next"], [repr(block) for block in EighthBlock.objects.filter(date="9001-4-20").all()])
        self.assertEqual(response.context["blocks_next_date"], datetime.datetime(9001, 4, 20).date())
        self.assertEqual(response.context["admin_page_title"], "Eighth Period Admin")
        self.assertEqual(response.context["signup_users_count"], get_user_model().objects.get_students().count())

    def test_transfer_students(self):
        self.make_admin()
        user = get_user_model().objects.get_or_create(username="awilliam")[0]
        block_a = self.add_block(date="9001-4-20", block_letter="A")
        block_b = self.add_block(date="9001-4-20", block_letter="B")
        act1 = self.add_activity(name="Test1")
        act2 = self.add_activity(name="Test2")
        schact_a1 = EighthScheduledActivity.objects.create(block=block_a, activity=act1)
        schact_a2 = EighthScheduledActivity.objects.create(block=block_a, activity=act2)
        schact_b1 = EighthScheduledActivity.objects.create(block=block_b, activity=act1)
        EighthSignup.objects.create(scheduled_activity=schact_a2, user=user)
        EighthSignup.objects.create(scheduled_activity=schact_b1, user=user)

        # Attempt move user from `schact_b1` to `schact_a1`, removing the signup for `schact_a2`
        self.client.post(reverse("eighth_admin_transfer_students_action"), {"source_act": schact_b1.id, "dest_act": schact_a1.id})
        self.assertEqual(len(user.eighthsignup_set.filter(scheduled_activity__block=block_a)), 1)
        self.assertEqual(user.eighthsignup_set.get(scheduled_activity__block=block_a).scheduled_activity, schact_a1)
        self.assertFalse(user.eighthsignup_set.filter(scheduled_activity__block=block_b).exists())

    def test_activity_stats(self):
        self.make_admin()
        user = get_user_model().objects.get_or_create(username="user1", graduation_year=get_senior_graduation_year())[0]
        block_a = self.add_block(date="2013-4-20", block_letter="A")
        block_b = self.add_block(date="2013-4-20", block_letter="B")
        act1 = self.add_activity(name="Test1")
        act2 = self.add_activity(name="Test2")
        schact_a = EighthScheduledActivity.objects.create(block=block_a, activity=act1)
        schact_b = EighthScheduledActivity.objects.create(block=block_b, activity=act1)
        EighthSignup.objects.create(scheduled_activity=schact_a, user=user)
        EighthSignup.objects.create(scheduled_activity=schact_b, user=user)

        response = self.client.post(
            reverse("eighth_statistics_multiple"),
            {
                "activities": [act1.id, act2.id],
                "lower": "",
                "upper": "",
                "start": "2020-10-01",
                "end": "2020-10-24",
                "freshmen": "on",
                "sophmores": "on",
                "juniors": "on",
                "seniors": "on",
            },
        )
        self.assertEqual(len(response.context["signed_up"]), 0)
        response = self.client.post(
            reverse("eighth_statistics_multiple"),
            {
                "activities": [act1.id, act2.id],
                "lower": "",
                "upper": "",
                "start": "2013-01-01",
                "end": "2020-10-24",
                "freshmen": "on",
                "sophmores": "on",
                "juniors": "on",
                "seniors": "on",
            },
        )
        self.assertEqual(len(response.context["signed_up"]), 1)
        self.assertEqual(response.context["signed_up"][0]["signups"], 2)

    def test_room_change(self):
        self.make_admin()
        act1 = EighthActivity.objects.create(name="Act1")
        act2 = EighthActivity.objects.create(name="Act2")
        room1 = EighthRoom.objects.create(name="Room 1", capacity=1)
        room2 = EighthRoom.objects.create(name="Room 2", capacity=1)
        act1.rooms.add(room1)
        act2.rooms.add(room2)
        self.client.post(
            reverse("eighth_admin_add_room"),
            {
                "name": "Room 3",
                "capacity": 1,
                "activities": [act2.id],
            },
        )
        self.assertEqual(len(act1.rooms.all()), 1)
        self.assertEqual(len(act2.rooms.all()), 2)
        self.client.post(
            reverse("eighth_admin_edit_room", args=[room2.id]),
            {
                "name": "Room 2",
                "capacity": 1,
                "activities": [act1.id],
            },
        )
        self.assertEqual(len(act1.rooms.all()), 2)
        self.assertEqual(len(act2.rooms.all()), 1)

    def test_eighth_room_utilization(self):
        """Ensure that the room utilization check filters properly."""
        self.make_admin()
        block1 = self.add_block(date="2015-01-01", block_letter="A")
        room1 = self.add_room(name="room1", capacity=1)
        act1 = self.add_activity(name="Test Activity 1", room=room1)
        schact1 = EighthScheduledActivity.objects.create(block=block1, activity=act1)
        schact1.rooms.add(room1)
        schact1.save()
        # Test filtering for room1
        response = self.client.get(reverse("eighth_admin_room_utilization", args=[block1.id, block1.id]), {"room": room1.id})
        self.assertEqual(list(response.context["scheduled_activities"]), [schact1])

    def test_eighth_location_view(self):
        self.make_admin()
        now = timezone.localtime()
        time_start = Time.objects.create(hour=now.time().hour, minute=now.time().minute)
        time_end = Time.objects.create(hour=now.time().hour + 1, minute=now.time().minute)
        block = Block.objects.create(name="8A", start=time_start, end=time_end, order=1)
        red_day = DayType.objects.create(name="red")
        red_day.blocks.add(block)
        Day.objects.create(date=now.today(), day_type=red_day)
        # This part is a little hacky. We can't get the location of a response without redirecting, so we:

        # first test that the redirect works
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("eighth_location"))

        # then allow client to follow the redirect in order to add the "seen_eighth_location" cookie
        response = self.client.get("/", follow=True)

        # finally ensure that the "seen_eighth_location" cookie now prevents the redirect
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
