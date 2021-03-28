import csv
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from intranet.utils.date import get_senior_graduation_year

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from ..views.attendance import generate_roster_pdf
from .eighth_test import EighthAbstractTest


class EighthAttendanceTestCase(EighthAbstractTest):
    """Test cases for ``views.attendance``."""

    def test_take_attendance(self):
        """ Makes sure that taking attendance for activites with multiple students signed up works. """
        self.make_admin()

        user1 = get_user_model().objects.create(
            username="user1", graduation_year=get_senior_graduation_year() + 1, student_id=12345, first_name="Test", last_name="User"
        )
        user2 = get_user_model().objects.create(
            username="user2", graduation_year=get_senior_graduation_year() + 1, student_id=12346, first_name="TestTwo", last_name="UserTwo"
        )
        user3 = get_user_model().objects.create(
            username="user3", graduation_year=get_senior_graduation_year() + 1, student_id=12347, first_name="TestThree", last_name="UserThree"
        )

        block1 = self.add_block(date="3000-11-11", block_letter="A")
        room1 = self.add_room(name="room1", capacity=5)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)

        schact1 = self.schedule_activity(act1.id, block1.id, capacity=5)
        schact1.attendance_taken = False
        schact1.add_user(user1)
        schact1.add_user(user2)
        schact1.add_user(user3)
        schact1.save()

        # Simulate taking attendance with user1 and user3 present, but user2 absent.
        response = self.client.post(reverse("eighth_take_attendance", args=[schact1.id]), data={user1.id: "on", user3.id: "on"})
        self.assertEqual(response.status_code, 302)

        # Make sure activity is marked as attendance taken.
        self.assertTrue(EighthScheduledActivity.objects.get(id=schact1.id).attendance_taken)

        # Make sure EighthSignup object hasn't been marked absent for user1.
        self.assertFalse(EighthSignup.objects.get(user=user1, scheduled_activity=schact1).was_absent)

        # Make sure EighthSignup object was marked absent for user2.
        self.assertTrue(EighthSignup.objects.get(user=user2, scheduled_activity=schact1).was_absent)

        # Make sure EighthSignup object hasn't been marked absent for user3.
        self.assertFalse(EighthSignup.objects.get(user=user3, scheduled_activity=schact1).was_absent)

    def test_take_attendance_clear_bit(self):
        """Tests the "clear attendance bit" feature."""
        # Schedule an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Take attendance
        scheduled.attendance_taken = True
        scheduled.save()

        # Log in
        self.make_admin()

        # Clear the bit
        response = self.client.post(
            reverse("eighth_take_attendance", kwargs={"scheduled_activity_id": scheduled.id}), data={"clear_attendance_bit": True}, follow=True
        )
        self.assertEqual(200, response.status_code)

        self.assertFalse(EighthScheduledActivity.objects.get(block=block, activity=activity).attendance_taken)

    def test_take_attendance_google_meet_csv(self):
        """ Make sure taking attendence through an uploaded Google Meet file works. """
        self.make_admin()
        user1 = get_user_model().objects.create(
            username="user1", graduation_year=get_senior_graduation_year() + 1, student_id=12345, first_name="Test", last_name="User"
        )
        user2 = get_user_model().objects.create(
            username="user2", graduation_year=get_senior_graduation_year() + 1, student_id=12346, first_name="TestTwo", last_name="UserTwo"
        )

        block1 = self.add_block(date="3000-11-11", block_letter="A")
        room1 = self.add_room(name="room1", capacity=5)

        act1 = self.add_activity(name="Test Activity 1")
        act1.rooms.add(room1)

        schact1 = self.schedule_activity(act1.id, block1.id, capacity=5)
        schact1.attendance_taken = False
        schact1.add_user(user1)
        schact1.add_user(user2)
        schact1.save()

        with tempfile.NamedTemporaryFile(mode="w+") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Email"])
            writer.writeheader()
            writer.writerow({"Name": "Test User", "Email": "12345@fcpsschools.net"})
            f.seek(0)
            self.client.post(reverse("eighth_take_attendance", args=[schact1.id]), {"attendance": f})

        # Make sure attendance has been marked as taken.
        self.assertTrue(EighthScheduledActivity.objects.get(id=schact1.id).attendance_taken)

        # Make sure EighthSignup object hasn't been marked absent for user1.
        self.assertFalse(EighthSignup.objects.get(user=user1, scheduled_activity=schact1).was_absent)

        # Make sure EighthSignup object was marked absent for user2.
        self.assertTrue(EighthSignup.objects.get(user=user2, scheduled_activity=schact1).was_absent)

        # Make sure bad file fails nicely with KeyError
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            writer = csv.DictWriter(f, fieldnames=["NotName", "NotEmail"])
            writer.writeheader()
            writer.writerow({"NotName": "Test User", "NotEmail": "12345@fcpsschools.net"})
            f.seek(0)
            response = self.client.post(reverse("eighth_take_attendance", args=[schact1.id]), {"attendance": f}, follow=True)

            self.assertIn(
                "Could not interpret file. Did you upload a Google Meet attendance report without modification?",
                list(map(str, list(response.context["messages"]))),
            )
            self.assertEqual(response.status_code, 200)

        # Make sure bad file fails nicely with IndexError
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Email"])
            writer.writeheader()
            writer.writerow({"Name": "User", "Email": "@fcpsschools.net"})
            f.seek(0)
            response = self.client.post(reverse("eighth_take_attendance", args=[schact1.id]), {"attendance": f}, follow=True)

            self.assertIn(
                "Could not interpret file. Did you upload a Google Meet attendance report without modification?",
                list(map(str, list(response.context["messages"]))),
            )
            self.assertEqual(response.status_code, 200)

        # Make sure bad file fails nicely with ValueError
        with tempfile.NamedTemporaryFile(mode="w+") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Email"])
            writer.writeheader()
            writer.writerow({"Name": 1, "Email": 5})
            f.seek(0)
            self.assertIn(
                "Could not interpret file. Did you upload a Google Meet attendance report without modification?",
                list(map(str, list(response.context["messages"]))),
            )
            self.assertEqual(response.status_code, 200)

    def test_roster_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.roster_view`."""

        # Schedule an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Log in, and just load the page
        user = self.login()
        user.user_type = "teacher"
        user.save()

        response = self.client.get(reverse("eighth_roster", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(scheduled, response.context["scheduled_activity"])
        self.assertEqual(0, response.context["viewable_members"].count())
        self.assertFalse(response.context["is_sponsor"])

        # Now, make this user the sponsor
        eighth_sponsor = EighthSponsor.objects.get_or_create(first_name="A", last_name="william", user=user)[0]
        scheduled.sponsors.add(eighth_sponsor)
        scheduled.save()

        response = self.client.get(reverse("eighth_roster", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(scheduled, response.context["scheduled_activity"])
        self.assertEqual(0, response.context["viewable_members"].count())
        self.assertTrue(response.context["is_sponsor"])

    def test_raw_roster_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.raw_roster_view`."""

        # Schedule an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Log in, and just load the page
        user = self.login()
        user.user_type = "teacher"
        user.save()

        response = self.client.get(reverse("eighth_raw_roster", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(scheduled, response.context["scheduled_activity"])
        self.assertEqual(0, response.context["viewable_members"].count())

    def test_raw_waitlist_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.raw_waitlist_view`."""

        # We don't use the waitlist anymore. But that doesn't mean I can test it.
        self.make_admin()

        # Schedule an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        response = self.client.get(reverse("eighth_raw_waitlist", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.context["ordered_waitlist"]))

    def test_generate_roster_pdf(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.generate_roster_pdf`"""

        # Make us an admin
        self.make_admin()

        # Schedule an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]

        # Make more blocks
        block2 = EighthBlock.objects.get_or_create(date=today, block_letter="test")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block2, activity=activity)[0]

        block3 = EighthBlock.objects.get_or_create(date=today, block_letter="testing")[0]
        scheduled3 = EighthScheduledActivity.objects.get_or_create(block=block3, activity=activity)[0]

        # Make a user
        user = get_user_model().objects.get_or_create(username="2021ttest", first_name="T", last_name="Test")[0]
        EighthSignup.objects.create(user=user, scheduled_activity=scheduled)

        # Generate the PDF
        generate_roster_pdf([scheduled.id, scheduled2.id, scheduled3.id])

        # We can't really parse this PDF to make sure it is fine though

    def test_eighth_absences_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.eighth_absences_view`."""

        # First, test as a student
        user = self.login("2021awilliam")
        user.user_type = "student"
        user.save()

        # Just load the page
        response = self.client.get(reverse("eighth_absences"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["user"])
        self.assertEqual(0, len(response.context["absences"]))

        # Give this student an eighth absence
        # Schedule an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        # Make a signup
        signup = EighthSignup.objects.create(user=user, scheduled_activity=scheduled, was_absent=True)

        # Now, make me an admin and try to find the user
        admin = self.make_admin()
        response = self.client.get(reverse("eighth_absences", kwargs={"user_id": user.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["user"])
        self.assertListEqual([signup], list(response.context["absences"]))

        # Try again with this user marked present
        signup.was_absent = False
        signup.save()

        response = self.client.get(reverse("eighth_absences"), data={"user": user.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(user, response.context["user"])
        self.assertListEqual([], list(response.context["absences"]))

        # Assert a redirect if not a student
        admin.user_type = "teacher"
        admin.save()
        response = self.client.get(reverse("eighth_absences"))
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_admin_dashboard"), response.url)

    def test_sponsor_schedule_widget_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.sponsor_schedule_widget_view`."""

        # Log in and load the page; the page should show that "you are not an eighth period sponsor"
        # because we are not one
        user = self.login()
        response = self.client.get(reverse("eighth_sponsor_schedule_widget"))
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.context["eighth_sponsor"])

        # Now, make us a sponsor
        user.user_type = "teacher"
        user.save()
        sponsor = EighthSponsor.objects.get_or_create(first_name="a", last_name="william", user=user)[0]

        response = self.client.get(reverse("eighth_sponsor_schedule_widget"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["eighth_sponsor"])
        self.assertEqual(0, len(response.context["sponsor_schedule"]))

        # Add some activities and blocks
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]
        scheduled.sponsors.add(sponsor)
        scheduled.save()

        response = self.client.get(reverse("eighth_sponsor_schedule_widget"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["eighth_sponsor"])
        self.assertEqual(1, len(response.context["sponsor_schedule"]))

        # Try defining date in a GET parameter
        response = self.client.get(reverse("eighth_sponsor_schedule_widget"), data={"date": today.isoformat()})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["eighth_sponsor"])
        self.assertEqual(1, len(response.context["sponsor_schedule"]))

        # If we try getting data for tomorrow, this should be zero
        response = self.client.get(reverse("eighth_sponsor_schedule_widget"), data={"date": (today + timezone.timedelta(days=1)).isoformat()})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["eighth_sponsor"])
        self.assertEqual(0, len(response.context["sponsor_schedule"]))

    def test_email_students_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.email_students_view`."""
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, attendance_taken=True)[0]

        self.login()
        response = self.client.get(reverse("eighth_email_students", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(404, response.status_code)  # Not an admin

        # Make us an admin then just load the page
        self.make_admin()

        response = self.client.get(reverse("eighth_email_students", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)

        # Test sending something
        response = self.client.post(
            reverse("eighth_email_students", kwargs={"scheduled_activity_id": scheduled.id}),
            data={"subject": "test email", "body": "this is a test"},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

    def test_teacher_choose_scheduled_activity_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.teacher_choose_scheduled_activity_view`."""

        # Make this user a teacher and a sponsor of an eighth period activity
        user = self.login()
        user.user_type = "teacher"
        user.save()
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        sponsor = EighthSponsor.objects.get_or_create(user=user, first_name="a", last_name="william")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        scheduled.sponsors.add(sponsor)
        scheduled.save()

        # Load the page.
        response = self.client.get(reverse("eighth_attendance_choose_scheduled_activity"))
        self.assertEqual(200, response.status_code)

        self.assertIn(str(block), response.content.decode("UTF-8"))

        # Now, POST the block ID to get to the "select activity" page
        # But, we are only sponsoring one activity, so we are redirected there

        response = self.client.post(
            reverse("eighth_attendance_choose_scheduled_activity"),
            data={"eighth_attendance_select_scheduled_activity_wizard-current_step": "block", "block-block": block.id},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_take_attendance", kwargs={"scheduled_activity_id": scheduled.id}), response.url)

        # Now, add another activity we're sponsoring
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity Two")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2)[0]
        scheduled2.sponsors.add(sponsor)
        scheduled2.save()

        # This should now 200 to the "select activity" page
        response = self.client.post(
            reverse("eighth_attendance_choose_scheduled_activity"),
            data={"eighth_attendance_select_scheduled_activity_wizard-current_step": "block", "block-block": block.id},
        )
        self.assertEqual(200, response.status_code)
        self.assertIn(activity.name, response.content.decode("UTF-8"))
        self.assertIn(activity2.name, response.content.decode("UTF-8"))

        # Now, POST the first activity
        response = self.client.post(
            reverse("eighth_attendance_choose_scheduled_activity"),
            data={"eighth_attendance_select_scheduled_activity_wizard-current_step": "activity", "activity-activity": activity.id},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_take_attendance", kwargs={"scheduled_activity_id": scheduled.id}), response.url)

        # What about "show past blocks this year"?
        yesterday = (timezone.localtime() - timezone.timedelta(days=1)).date()
        block_old = EighthBlock.objects.get_or_create(date=yesterday, block_letter="A")[0]

        # block_old should not show in this list because it is not "show all blocks"
        response = self.client.get(reverse("eighth_attendance_choose_scheduled_activity"))
        self.assertEqual(200, response.status_code)

        self.assertIn(str(block), response.content.decode("UTF-8"))
        self.assertNotIn(str(block_old), response.content.decode("UTF-8"))

        # Now, try show_all_blocks = 1 and both blocks should show
        response = self.client.get(reverse("eighth_attendance_choose_scheduled_activity"), data={"show_all_blocks": True})
        self.assertEqual(200, response.status_code)

        self.assertIn(str(block), response.content.decode("UTF-8"))
        self.assertIn(str(block_old), response.content.decode("UTF-8"))

        # Test default_activity
        # response = self.client.get(reverse("eighth_attendance_choose_scheduled_activity"),
        #                            data={"eighth_attendance_select_scheduled_activity_wizard-current_step": "activity",
        #                                   "block-block": block.id, "default_activity": activity.id})
        # self.assertEqual(200, response.status_code)
        # self.assertIn(str(activity), response.content.decode("UTF-8"))

    def test_attendance_export_csv(self):
        """Tests the "export CSV" function in :func:`~intranet.apps.eighth.views.attendance.take_attendance_view`."""

        # Make this user a teacher and a sponsor of an eighth period activity
        user = self.login()
        user.user_type = "teacher"
        user.save()
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        sponsor = EighthSponsor.objects.get_or_create(user=user, first_name="a", last_name="william")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        scheduled.sponsors.add(sponsor)
        scheduled.save()

        # Get a CSV - should be empty because there are no signups (yet)
        response = self.client.get(reverse("eighth_admin_export_attendance_csv", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)

        # Parse CSV - should be empty
        raw_output = response.content.decode("UTF-8").split("\n")
        reader = csv.DictReader(raw_output)
        self.assertEqual(0, len(list(reader)))
        self.assertEqual(
            [
                "Block",
                "Activity",
                "Name",
                "FCPS ID",
                "Student ID",
                "Grade",
                "Email",
                "Locked",
                "Rooms",
                "Sponsors",
                "Attendance Taken",
                "Present",
                "Had Pass",
            ],
            reader.fieldnames,
        )

        # Add a student signup
        student = get_user_model().objects.get_or_create(username="2021awilliam", first_name="Angela", last_name="William", student_id=1234567)[0]
        EighthSignup.objects.get_or_create(user=student, scheduled_activity=scheduled)

        response = self.client.get(reverse("eighth_admin_export_attendance_csv", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(200, response.status_code)

        raw_output = response.content.decode("UTF-8").split("\n")
        reader = csv.DictReader(raw_output)
        reader_contents = list(reader)
        self.assertEqual(1, len(reader_contents))
        self.assertEqual(
            {
                "Block": str(block),
                "Activity": str(activity),
                "Name": "William, Angela",
                "FCPS ID": "1234567",
                "Student ID": str(student.id),
                "Grade": str(student.grade.number),
                "Email": student.tj_email,
                "Locked": "False",
                "Rooms": "",
                "Sponsors": "william",
                "Attendance Taken": "False",
                "Present": "N/A",
                "Had Pass": "N/A",
            },
            reader_contents[0],
        )

    def test_accept_pass_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.accept_pass_view`."""

        # Create an activity and a late signup
        user = self.login()
        user.user_type = "teacher"
        user.save()
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A", locked=True)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        sponsor = EighthSponsor.objects.get_or_create(user=user, first_name="a", last_name="william")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        scheduled.sponsors.add(sponsor)
        scheduled.save()

        student = get_user_model().objects.get_or_create(username="2021awilliam", first_name="Angela", last_name="William", student_id=1234567)[0]
        signup = EighthSignup.objects.get_or_create(user=student, scheduled_activity=scheduled, after_deadline=True)[0]

        # POST to that page and reject the pass
        response = self.client.post(reverse("eighth_accept_pass", kwargs={"signup_id": signup.id}), data={"status": "reject"})
        self.assertEqual(302, response.status_code)  # to attendance page

        # Ensure that the signup was marked absent and pass accepted
        self.assertTrue(EighthSignup.objects.get(id=signup.id).pass_accepted)
        self.assertTrue(EighthSignup.objects.get(id=signup.id).was_absent)

        # Now, try accepting
        response = self.client.post(reverse("eighth_accept_pass", kwargs={"signup_id": signup.id}), data={"status": "accept"})
        self.assertEqual(302, response.status_code)  # to attendance page

        # Ensure that the signup was NOT marked absent and pass accepted
        self.assertTrue(EighthSignup.objects.get(id=signup.id).pass_accepted)
        self.assertFalse(EighthSignup.objects.get(id=signup.id).was_absent)

    def test_accept_all_passes_view(self):
        """Tests :func:`~intranet.apps.eighth.views.attendance.accept_all_passes_view`."""

        # Very similar to test_accept_pass_view, but we have multiple passes to accept
        user = self.login()
        user.user_type = "teacher"
        user.save()
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A", locked=True)[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        sponsor = EighthSponsor.objects.get_or_create(user=user, first_name="a", last_name="william")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
        scheduled.sponsors.add(sponsor)
        scheduled.save()

        student1 = get_user_model().objects.get_or_create(username="2021awilliam", first_name="Angela", last_name="William", student_id=1234567)[0]
        signup1 = EighthSignup.objects.get_or_create(user=student1, scheduled_activity=scheduled, after_deadline=True)[0]
        student2 = get_user_model().objects.get_or_create(username="2022awilliam", first_name="Angela", last_name="William", student_id=1234568)[0]
        signup2 = EighthSignup.objects.get_or_create(user=student2, scheduled_activity=scheduled, after_deadline=True)[0]

        response = self.client.post(reverse("eighth_accept_all_passes", kwargs={"scheduled_activity_id": scheduled.id}))
        self.assertEqual(302, response.status_code)  # to attendance page

        # Ensure that the signups were NOT marked absent and pass accepted
        self.assertTrue(EighthSignup.objects.get(id=signup1.id).pass_accepted)
        self.assertFalse(EighthSignup.objects.get(id=signup1.id).was_absent)
        self.assertTrue(EighthSignup.objects.get(id=signup2.id).pass_accepted)
        self.assertFalse(EighthSignup.objects.get(id=signup2.id).was_absent)
