from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ...models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..eighth_test import EighthAbstractTest


class EighthAdminSchedulingTest(EighthAbstractTest):
    def test_schedule_activity_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.scheduling.schedule_activity_view`."""

        self.make_admin()

        # Add a block and an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        EighthBlock.objects.get_or_create(date=today, block_letter="B")
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_schedule_activity"))
        self.assertEqual(200, response.status_code)

        # Load the page and select the activity
        response = self.client.get(reverse("eighth_admin_schedule_activity"), data={"activity": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(activity, response.context["activity"])
        self.assertEqual(block, response.context["rows"][0][0])

        # Schedule this activity
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": True,
                "form-0-capacity": 5,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5).count())

        # Cancel this activity
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": False,
                "form-0-capacity": 5,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5, cancelled=True).count())

        # Unschedule this activity (i.e. delete it)
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": False,
                "form-0-unschedule": True,
                "form-0-capacity": 5,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(0, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5).count())

        # Test both blocks scheduling
        activity.both_blocks = True
        activity.save()
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": True,
                "form-0-capacity": 5,
                "form-0-both_blocks": True,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5, both_blocks=True).count())

        # Sign someone up for this activity
        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        signup = EighthSignup.objects.get_or_create(
            user=user1, scheduled_activity=EighthScheduledActivity.objects.get(block=block, activity=activity, capacity=5, both_blocks=True)
        )[0]

        # Cancelling should still work
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": False,
                "form-0-capacity": 5,
                "form-0-both_blocks": True,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            1, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5, cancelled=True, both_blocks=True).count()
        )

        # but deleting should not
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": False,
                "form-0-unschedule": True,
                "form-0-capacity": 5,
                "form-0-both_blocks": True,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            1, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5, cancelled=True, both_blocks=True).count()
        )

        # Remove the signup
        signup.delete()

        # Try again, the scheduled activity should be deleted
        response = self.client.post(
            reverse("eighth_admin_schedule_activity"),
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MAX_NUM_FORMS": "",
                "form-0-block": block.id,
                "form-0-activity": activity.id,
                "form-0-scheduled": False,
                "form-0-unschedule": True,
                "form-0-capacity": 5,
                "form-0-both_blocks": True,
            },
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            0, EighthScheduledActivity.objects.filter(block=block, activity=activity, capacity=5, cancelled=True, both_blocks=True).count()
        )

    def test_show_activity_schedule_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.scheduling.show_activity_schedule_view`."""

        self.make_admin()

        # Add an activity and a block and schedule it
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_view_activity_schedule"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([activity], list(response.context["activities"]))

        # Select the activity
        response = self.client.get(reverse("eighth_admin_view_activity_schedule"), data={"activity": activity.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(activity, response.context["activity"])
        self.assertEqual([scheduled], list(response.context["scheduled_activities"]))

    def test_distribute_students_view(self):
        # TODO: does this view even work?
        self.make_admin()
        response = self.client.get(reverse("eighth_admin_distribute_students"))
        self.assertEqual(200, response.status_code)

    def test_transfer_students(self):
        """Tests the transfer students views."""

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

        # Load the page
        response = self.client.get(reverse("eighth_admin_transfer_students"))
        self.assertEqual(200, response.status_code)

        # POST the first step (select block to transfer from)
        response = self.client.post(
            reverse("eighth_admin_transfer_students"),
            data={"eighth_admin_transfer_students_wizard-current_step": "block_1", "block_1-block": block_b.id},
        )
        self.assertEqual(200, response.status_code)

        # POST the second step (select activity to transfer from)
        response = self.client.post(
            reverse("eighth_admin_transfer_students"),
            data={"eighth_admin_transfer_students_wizard-current_step": "activity_1", "activity_1-activity": act1.id},
        )
        self.assertEqual(200, response.status_code)

        # POST the third step (select block to transfer to)
        response = self.client.post(
            reverse("eighth_admin_transfer_students"),
            data={"eighth_admin_transfer_students_wizard-current_step": "block_2", "block_2-block": block_a.id},
        )
        self.assertEqual(200, response.status_code)

        # POST the fourth step (select activity to transfer to)
        response = self.client.post(
            reverse("eighth_admin_transfer_students"),
            data={"eighth_admin_transfer_students_wizard-current_step": "activity_2", "activity_2-activity": act1.id},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_admin_transfer_students_action") + f"?source_act={schact_b1.id}&dest_act={schact_a1.id}", response.url)

        # GET the "confirm" page
        response = self.client.get(reverse("eighth_admin_transfer_students_action"), data={"source_act": schact_b1.id, "dest_act": schact_a1.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(schact_b1, response.context["source_act"])
        self.assertEqual(schact_a1, response.context["dest_act"])

        # Attempt move user from `schact_b1` to `schact_a1`, removing the signup for `schact_a2`
        self.client.post(reverse("eighth_admin_transfer_students_action"), {"source_act": schact_b1.id, "dest_act": schact_a1.id})
        self.assertEqual(len(user.eighthsignup_set.filter(scheduled_activity__block=block_a)), 1)
        self.assertEqual(user.eighthsignup_set.get(scheduled_activity__block=block_a).scheduled_activity, schact_a1)
        self.assertFalse(user.eighthsignup_set.filter(scheduled_activity__block=block_b).exists())

    def test_remove_duplicates_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.scheduling.remove_duplicates_view`."""

        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_remove_duplicates"))
        self.assertEqual(200, response.status_code)

        # POST to the page
        response = self.client.post(reverse("eighth_admin_remove_duplicates"))
        self.assertEqual(302, response.status_code)
