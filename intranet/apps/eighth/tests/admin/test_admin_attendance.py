import csv

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from intranet.utils.date import get_senior_graduation_year

from ...models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup
from ..eighth_test import EighthAbstractTest


class EighthAdminAttendanceTest(EighthAbstractTest):
    def test_take_attendance_zero(self):
        """ Make sure all activities with zero students are marked as having attendance taken when button is pressed. """
        self.make_admin()
        block1 = self.add_block(date="3000-11-11", block_letter="A")

        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)
        schact1.attendance_taken = False
        schact1.save()

        response = self.client.post(
            reverse("eighth_admin_view_activities_without_attendance") + "?" + urlencode({"block": block1.id}), {"take_attendance_zero": "1"}
        )
        self.assertEqual(response.status_code, 302)

        # Make sure activity is marked as attendance taken.
        self.assertTrue(EighthScheduledActivity.objects.get(id=schact1.id).attendance_taken)

    def test_take_attendance_cancelled(self):
        """ Make sure students in a cancelled activity are marked as absent when the button is pressed. """
        self.make_admin()
        user1 = get_user_model().objects.create(username="user1", graduation_year=get_senior_graduation_year() + 1)
        block1 = self.add_block(date="3000-11-11", block_letter="A")

        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)
        schact1.attendance_taken = False

        schact1.add_user(user1)

        schact1.cancelled = True
        schact1.save()

        response = self.client.post(
            reverse("eighth_admin_view_activities_without_attendance") + "?" + urlencode({"block": block1.id}), {"take_attendance_cancelled": "1"}
        )
        self.assertEqual(response.status_code, 302)

        # Make sure attendance has been marked as taken.
        self.assertTrue(EighthScheduledActivity.objects.get(id=schact1.id).attendance_taken)

        # Make sure EighthSignup object has been marked as absent.
        self.assertTrue(EighthSignup.objects.get(user=user1, scheduled_activity=schact1).was_absent)

        # Make sure student has correct number of absences.
        self.assertEqual(get_user_model().objects.get(id=user1.id).absence_count(), 1)

    def test_activities_without_attendance_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.activities_without_attendance_view`."""

        self.make_admin()

        # Most of the functionality was tested above...
        response = self.client.get(reverse("eighth_admin_view_activities_without_attendance"))
        self.assertEqual(200, response.status_code)

    def test_delinquent_students_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.delinquent_students_view`."""

        self.make_admin()

        # First, load the page
        response = self.client.get(reverse("eighth_admin_view_delinquent_students"))
        self.assertEqual(200, response.status_code)

        # Test with empty set of students (absences)
        EighthSignup.objects.all().delete()

        response = self.client.get(
            reverse("eighth_admin_view_delinquent_students"),
            data={"lower": 1, "upper": 100, "freshmen": "on", "sophomores": "on", "juniors": "on", "seniors": "on"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.context["delinquents"])

        # Add an absence
        user = get_user_model().objects.get_or_create(username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student")[0]
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled, was_absent=True)

        response = self.client.get(
            reverse("eighth_admin_view_delinquent_students"),
            data={"lower": 1, "upper": 100, "freshmen": "on", "sophomores": "on", "juniors": "on", "seniors": "on"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([{"user": user, "absences": 1}], response.context["delinquents"])

        # Exclude seniors
        response = self.client.get(
            reverse("eighth_admin_view_delinquent_students"), data={"lower": 1, "upper": 100, "freshmen": "on", "sophomores": "on", "juniors": "on"}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.context["delinquents"])

        # Test CSV output
        response = self.client.get(
            reverse("eighth_admin_download_delinquent_students_csv"),
            data={"lower": 1, "upper": 100, "freshmen": "on", "sophomores": "on", "juniors": "on", "seniors": "on"},
        )
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual(reader_contents[0]["TJ Email"], "2021awilliam@tjhsst.edu")
        self.assertEqual(reader_contents[0]["Absences"], "1")

    def test_no_signups_roster(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.no_signups_roster`."""

        admin_user = self.make_admin()
        admin_user.user_type = "teacher"
        admin_user.save()

        # Add a block
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)

        # Load the page
        response = self.client.get(reverse("eighth_admin_no_signups_roster", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.context["users"])

        # Test CSV output
        response = self.client.get(reverse("eighth_admin_no_signups_csv", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(0, len(reader_contents))

        # Add a user
        user = get_user_model().objects.get_or_create(username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student")[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_no_signups_roster", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual([user], response.context["users"])

        # Test CSV output
        response = self.client.get(reverse("eighth_admin_no_signups_csv", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual(reader_contents[0]["TJ Email"], "2021awilliam@tjhsst.edu")

    def test_after_deadline_signup_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.after_deadline_signup_view`."""

        admin_user = self.make_admin()
        admin_user.user_type = "teacher"
        admin_user.save()

        # Add a block
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_view_after_deadline_signups"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], list(response.context["signups"]))

        # Make a user and a late signup
        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled, after_deadline=True)

        # Load the page
        response = self.client.get(reverse("eighth_admin_view_after_deadline_signups"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([signup], list(response.context["signups"]))

        # Test CSV output
        response = self.client.get(reverse("eighth_admin_download_after_deadline_signups_csv"))
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual("William", reader_contents[0]["Last Name"])
        self.assertEqual(str(block), reader_contents[0]["Block"])

    def test_migrate_outstanding_passes_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.migrate_outstanding_passes_view`."""

        self.make_admin()

        EighthSignup.objects.all().delete()
        EighthBlock.objects.all().delete()
        EighthActivity.objects.all().delete()

        # First, load the page
        response = self.client.get(reverse("eighth_admin_migrate_outstanding_passes"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], list(response.context["blocks"]))

        # Add a block, activity, and a late signup
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled, after_deadline=True, pass_accepted=False)

        # Load the page
        response = self.client.get(reverse("eighth_admin_migrate_outstanding_passes"))
        self.assertEqual(200, response.status_code)
        self.assertEqual([block], list(response.context["blocks"]))

        # POST something invalid, it should 404
        response = self.client.post(reverse("eighth_admin_migrate_outstanding_passes"))  # missing block number
        self.assertEqual(404, response.status_code)

        # Now POST the block ID with it and the signup should migrate
        response = self.client.post(reverse("eighth_admin_migrate_outstanding_passes"), data={"block": block.id})
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, EighthActivity.objects.filter(name="Z - 8th Period Pass Not Received").count())
        self.assertEqual(
            EighthScheduledActivity.objects.get(activity__name="Z - 8th Period Pass Not Received", block=block),
            EighthSignup.objects.get(id=signup.id).scheduled_activity,
        )

    def test_out_of_building_schedules_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.out_of_building_schedules_view`."""

        self.make_admin()

        # First just load the page
        response = self.client.get(reverse("eighth_admin_export_out_of_building_schedules"))
        self.assertEqual(200, response.status_code)

        # Add a block and the "out of building" room, and an activity set to that room
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        room = EighthRoom.objects.get_or_create(name="Out of Building", capacity=5000)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        activity.rooms.add(room)
        activity.save()
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        # Load the page with that block
        response = self.client.get(reverse("eighth_admin_export_out_of_building_schedules"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual([], list(response.context["signups"]))

        # Add a user with a signup
        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled)

        # Load the page with that block
        response = self.client.get(reverse("eighth_admin_export_out_of_building_schedules"), data={"block": block.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual([signup], list(response.context["signups"]))

        # Test CSV
        response = self.client.get(reverse("eighth_admin_export_out_of_building_schedules_csv", kwargs={"block_id": block.id}))
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual("William", reader_contents[0]["Last Name"])
        self.assertEqual(str(activity.id), reader_contents[0]["Activity ID"])

    def test_clear_absence_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.clear_absence_view`."""

        self.make_admin()

        # Add a user with an absence
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled, was_absent=True)

        response = self.client.post(reverse("eighth_admin_clear_absence", kwargs={"signup_id": signup.id}))
        self.assertEqual(302, response.status_code)  # to dashboard

        self.assertFalse(EighthSignup.objects.get(id=signup.id).was_absent)

    def test_open_passes_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.attendance.open_passes_view`."""

        self.make_admin()

        # Load the page
        response = self.client.get(reverse("eighth_admin_view_open_passes"))
        self.assertEqual(200, response.status_code)

        # Make a student with a pass
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        user = get_user_model().objects.get_or_create(
            username="2021awilliam", graduation_year=get_senior_graduation_year(), user_type="student", last_name="William"
        )[0]
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled, after_deadline=True)

        # Accept the pass
        response = self.client.post(reverse("eighth_admin_view_open_passes"), data={signup.id: "accept"})
        self.assertEqual(200, response.status_code)

        self.assertTrue(EighthSignup.objects.get(id=signup.id).pass_accepted)
        self.assertFalse(EighthSignup.objects.get(id=signup.id).was_absent)

        # Now, reject the pass
        response = self.client.post(reverse("eighth_admin_view_open_passes"), data={signup.id: "reject"})
        self.assertEqual(200, response.status_code)

        self.assertTrue(EighthSignup.objects.get(id=signup.id).pass_accepted)
        self.assertTrue(EighthSignup.objects.get(id=signup.id).was_absent)

        # Test the CSV view
        # but first, reset the pass
        signup = EighthSignup.objects.get(id=signup.id)
        signup.pass_accepted = False
        signup.was_absent = False
        signup.save()
        response = self.client.get(reverse("eighth_admin_view_open_passes_csv"))
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual("0", reader_contents[0]["Absences"])
