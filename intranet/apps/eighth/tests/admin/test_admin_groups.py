import csv

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from intranet.apps.groups.models import Group
from intranet.utils.date import get_senior_graduation_year

from ...models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..eighth_test import EighthAbstractTest


class EighthAdminGroupsTest(EighthAbstractTest):
    def test_add_group_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.add_group_view`."""

        self.make_admin()

        # GET should not work
        response = self.client.get(reverse("eighth_admin_add_group"))
        self.assertEqual(405, response.status_code)

        # POST a new group
        response = self.client.post(reverse("eighth_admin_add_group"), data={"name": "test group 1"})
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_admin_edit_group", kwargs={"group_id": Group.objects.get(name="test group 1").id}), response.url)

    def test_edit_group_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.edit_group_view`."""

        self.make_admin()

        # Add a group
        group = Group.objects.get_or_create(name="test group 2")[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_edit_group", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)

        # Addding users tested in test_add_member_to_group_view below

        # Add three users
        user1 = get_user_model().objects.get_or_create(username="2021ttest", first_name="Tommy", last_name="Test")[0]
        user2 = get_user_model().objects.get_or_create(username="2021ttest1", first_name="Thomas", last_name="Test")[0]
        user3 = get_user_model().objects.get_or_create(username="2021awilliam", first_name="A", last_name="William")[0]

        for user in [user1, user2, user3]:
            user.groups.add(group)
            user.save()

        # Load the page
        response = self.client.get(reverse("eighth_admin_edit_group", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.context["member_count"])

        # Test filtering by Ion username
        response = self.client.get(reverse("eighth_admin_edit_group", kwargs={"group_id": group.id}), data={"q": "2021ttest,2021ttest1"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.context["member_count"])

        # Delete all the members
        response = self.client.post(reverse("eighth_admin_edit_group", kwargs={"group_id": group.id}), data={"remove_all": True}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.context["member_count"])

    def test_upload_group_members_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.upload_group_members_view`."""

        self.make_admin()

        # Add a group
        group = Group.objects.get_or_create(name="test group 3")[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual("upload", response.context["stage"])

        # Add some users
        user1 = get_user_model().objects.get_or_create(username="2021ttest", first_name="Tommy", last_name="Test")[0]
        user2 = get_user_model().objects.get_or_create(username="2021ttest1", first_name="Thomas", last_name="Test", student_id=1234567)[0]
        user3 = get_user_model().objects.get_or_create(username="2021awilliam", first_name="A", last_name="William")[0]

        # Add user1 by file upload
        file_obj = SimpleUploadedFile("users.csv", "2021ttest\n".encode("UTF-8"), content_type="text/csv")
        response = self.client.post(reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}), data={"file": file_obj})
        self.assertEqual(200, response.status_code)
        self.assertEqual("parse", response.context["stage"])
        self.assertEqual([["2021ttest", user1]], response.context["sure_users"])
        self.assertEqual([], response.context["unsure_users"])

        # Continue to add user1
        response = self.client.post(reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}), data={"user_id": [user1.id]})
        self.assertEqual(302, response.status_code)
        self.assertEqual([user1], list(Group.objects.get(id=group.id).user_set.all()))

        # Add user2 by text input
        response = self.client.post(
            reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}),
            data={"filetext": "Thomas Test,1234567,asdlfjadsksajkdfsa\nthisisatest,1236478,anditwontmatch\n"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("parse", response.context["stage"])
        self.assertEqual([["Thomas Test,1234567,asdlfjadsksajkdfsa", user2]], response.context["sure_users"])
        self.assertEqual([["thisisatest,1236478,anditwontmatch", []]], response.context["unsure_users"])

        # Continue to add user2
        response = self.client.post(reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}), data={"user_id": [user2.id]})
        self.assertEqual(302, response.status_code)
        self.assertEqual([user1, user2], list(Group.objects.get(id=group.id).user_set.all()))

        # Add user3 by "import other group"
        group2 = Group.objects.get_or_create(name="test group 4")[0]
        user3.groups.add(group2)
        user3.save()

        response = self.client.get(reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual("upload", response.context["stage"])
        self.assertIn(group2, response.context["all_groups"])

        response = self.client.post(reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}), data={"import_group": group2.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual("import_confirm", response.context["stage"])
        self.assertEqual(group2, response.context["import_group"])

        # Continue to add user3
        response = self.client.post(
            reverse("eighth_admin_upload_group_members", kwargs={"group_id": group.id}),
            data={"import_group": group2.id, "import_confirm": "import_confirm"},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual([user1, user2, user3], list(Group.objects.get(id=group.id).user_set.all()))

    def test_delete_group_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.delete_group_view`."""

        self.make_admin()

        # Add a group with some users
        group = Group.objects.get_or_create(name="test group 5")[0]
        user1 = get_user_model().objects.get_or_create(username="2021ttest", first_name="Tommy", last_name="Test")[0]
        user2 = get_user_model().objects.get_or_create(username="2021ttest1", first_name="Thomas", last_name="Test", student_id=1234567)[0]
        user3 = get_user_model().objects.get_or_create(username="2021awilliam", first_name="A", last_name="William")[0]
        for member in [user1, user2, user3]:
            member.groups.add(group)
            member.save()

        # Load the page
        response = self.client.get(reverse("eighth_admin_delete_group", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)

        # Delete the group
        response = self.client.post(reverse("eighth_admin_delete_group", kwargs={"group_id": group.id}))
        self.assertEqual(302, response.status_code)
        self.assertEqual(0, Group.objects.filter(id=group.id).count())

    def test_download_group_csv_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.download_group_csv_view`."""

        self.make_admin()

        # Add a group with some users
        group = Group.objects.get_or_create(name="test group 5")[0]
        user1 = get_user_model().objects.get_or_create(username="2021ttest", first_name="Tommy", last_name="Test", student_id=1234568)[0]
        user2 = get_user_model().objects.get_or_create(username="2021ttest1", first_name="Thomas", last_name="Test", student_id=1234567)[0]
        user3 = get_user_model().objects.get_or_create(username="2021awilliam", first_name="A", last_name="William", student_id=1234569)[0]
        for member in [user1, user2, user3]:
            member.groups.add(group)
            member.save()

        response = self.client.get(reverse("eighth_admin_download_group_csv", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)

        reader = csv.DictReader(response.content.decode("UTF-8").split("\n"))
        reader_contents = list(reader)
        self.assertEqual(3, len(reader_contents))

    def test_eighth_admin_signup_group(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.eighth_admin_signup_group`."""

        self.make_admin()

        # Add a group with some users
        group = Group.objects.get_or_create(name="test group 5")[0]
        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user2 = get_user_model().objects.get_or_create(
            username="2021ttest1",
            first_name="Thomas",
            last_name="Test",
            student_id=1234567,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user3 = get_user_model().objects.get_or_create(
            username="2021awilliam",
            first_name="A",
            last_name="William",
            student_id=1234569,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        for member in [user1, user2, user3]:
            member.groups.add(group)
            member.save()

        # Add a block with an activity
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity, capacity=5)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_signup_group", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)

        # Select a block
        response = self.client.post(
            reverse("eighth_admin_signup_group", kwargs={"group_id": group.id}),
            data={"eighth_admin_sign_up_group_wizard-current_step": "block", "block-block": block.id},
        )
        self.assertEqual(200, response.status_code)

        # Select an activity
        response = self.client.post(
            reverse("eighth_admin_signup_group", kwargs={"group_id": group.id}),
            data={"eighth_admin_sign_up_group_wizard-current_step": "activity", "activity-activity": activity.id},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("eighth_admin_signup_group_action", kwargs={"group_id": group.id, "schact_id": scheduled.id}), response.url)

        # Load the confirmation page
        response = self.client.get(reverse("eighth_admin_signup_group_action", kwargs={"group_id": group.id, "schact_id": scheduled.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(scheduled, response.context["scheduled_activity"])
        self.assertEqual(group, response.context["group"])

        # Perform the signup synchronously
        response = self.client.post(
            reverse("eighth_admin_signup_group_action", kwargs={"group_id": group.id, "schact_id": scheduled.id}), data={"confirm": "confirm"}
        )
        self.assertEqual(302, response.status_code)

        # Verify signups
        for user in [user1, user2, user3]:
            self.assertEqual(1, EighthSignup.objects.filter(user=user, scheduled_activity=scheduled).count())

    def test_eighth_admin_distribute_group(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.eighth_admin_distribute_group` - the wizard only."""

        self.make_admin()

        # Add a group, some users, and two activities
        group = Group.objects.get_or_create(name="test group 6")[0]
        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user2 = get_user_model().objects.get_or_create(
            username="2021ttest1",
            first_name="Thomas",
            last_name="Test",
            student_id=1234567,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user3 = get_user_model().objects.get_or_create(
            username="2021awilliam",
            first_name="A",
            last_name="William",
            student_id=1234569,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        for member in [user1, user2, user3]:
            member.groups.add(group)
            member.save()

        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity1, capacity=5)[0]
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2, capacity=5)[0]

        # Load the page
        response = self.client.get(reverse("eighth_admin_distribute_group", kwargs={"group_id": group.id}))
        self.assertEqual(200, response.status_code)

        # Select the block
        response = self.client.post(
            reverse("eighth_admin_distribute_group", kwargs={"group_id": group.id}),
            data={"eighth_admin_distribute_group_wizard-current_step": "block", "block-block": block.id},
        )
        self.assertEqual(200, response.status_code)

        # Select the activities
        response = self.client.post(
            reverse("eighth_admin_distribute_group", kwargs={"group_id": group.id}),
            data={"eighth_admin_distribute_group_wizard-current_step": "activity", "activity-activities": [activity1.id, activity2.id]},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            reverse("eighth_admin_distribute_action") + f"?&schact={scheduled1.id}&schact={scheduled2.id}&group={group.id}", response.url
        )

        # Actually signing up students is tested later.

    def test_eighth_admin_distribute_unsigned(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.eighth_admin_distribute_unsigned` - the wizard only."""

        get_user_model().objects.all().delete()
        self.make_admin()

        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity1, capacity=5)[0]
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2, capacity=5)[0]

        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user2 = get_user_model().objects.get_or_create(
            username="2021ttest1",
            first_name="Thomas",
            last_name="Test",
            student_id=1234567,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user3 = get_user_model().objects.get_or_create(
            username="2021awilliam",
            first_name="A",
            last_name="William",
            student_id=1234569,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]

        # There should be two students not signed up.

        # Load the page
        response = self.client.get(reverse("eighth_admin_distribute_unsigned"))
        self.assertEqual(200, response.status_code)

        # Select the block
        response = self.client.post(
            reverse("eighth_admin_distribute_unsigned"), data={"eighth_admin_distribute_group_wizard-current_step": "block", "block-block": block.id}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([user1, user2, user3], list(response.context["users"]))

        # Select the two activities
        response = self.client.post(
            reverse("eighth_admin_distribute_unsigned"),
            data={"eighth_admin_distribute_group_wizard-current_step": "activity", "activity-activities": [activity1.id, activity2.id]},
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            reverse("eighth_admin_distribute_action") + f"?&schact={scheduled1.id}&schact={scheduled2.id}&unsigned=1&block={block.id}", response.url
        )

        # Actually signing up students is tested later - actually,
        # right below this, in test_eighth_admin_distribute_action.

    def test_eighth_admin_distribute_action(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.eighth_admin_distribute_action`"""

        get_user_model().objects.all().delete()
        self.make_admin()

        # Add a block, activities, and some users
        today = timezone.localtime().date()
        block = EighthBlock.objects.get_or_create(date=today, block_letter="A")[0]
        activity1 = EighthActivity.objects.get_or_create(name="Test Activity")[0]
        scheduled1 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity1, capacity=5)[0]
        activity2 = EighthActivity.objects.get_or_create(name="Test Activity 2")[0]
        scheduled2 = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity2, capacity=5)[0]

        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user2 = get_user_model().objects.get_or_create(
            username="2021ttest1",
            first_name="Thomas",
            last_name="Test",
            student_id=1234567,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user3 = get_user_model().objects.get_or_create(
            username="2021awilliam",
            first_name="A",
            last_name="William",
            student_id=1234569,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]

        # Start by adding all the users to a group, and distributing that way
        group = Group.objects.get_or_create(name="test group 7")[0]
        for member in [user1, user2, user3]:
            member.groups.add(group)
            member.save()

        # Load the page
        response = self.client.get(reverse("eighth_admin_distribute_action"), data={"schact": [scheduled1.id, scheduled2.id], "group": group.id})
        self.assertEqual(200, response.status_code)
        self.assertEqual(group, response.context["group"])
        self.assertEqual([scheduled1, scheduled2], list(response.context["schacts"]))
        self.assertEqual([user1, user2, user3], list(response.context["users"]))

        # Perform a signup but manually specifying which user gets which activity
        response = self.client.post(
            reverse("eighth_admin_distribute_action"),
            data={"users": True, f"schact{scheduled1.id}": [user1.id, user2.id], f"schact{scheduled2.id}": [user3.id], "schact12304978": user3.id},
        )  # invalid shouldn't affect this
        self.assertEqual(302, response.status_code)

        for user in [user1, user2]:
            self.assertEqual(1, EighthSignup.objects.filter(user=user, scheduled_activity=scheduled1).count())
        self.assertEqual(1, EighthSignup.objects.filter(user=user3, scheduled_activity=scheduled2).count())

        # Delete the signups for user1 and user2
        EighthSignup.objects.filter(user__in=[user1, user2]).delete()

        # Try again but now with unsigned students
        response = self.client.get(
            reverse("eighth_admin_distribute_action"), data={"schact": [scheduled1.id, scheduled2.id], "unsigned": True, "block": block.id}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([user1, user2], list(response.context["users"]))

        # Actually performing the signup is redundant

    def test_add_member_to_group_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.add_member_to_group_view`"""

        self.make_admin()

        # Add a group and a user not in that group
        group = Group.objects.get_or_create(name="test group 8")[0]
        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]

        # POST to that page by student ID
        response = self.client.post(reverse("eighth_admin_add_member_to_group", kwargs={"group_id": group.id}), data={"query": 1234568})
        self.assertEqual(302, response.status_code)
        self.assertIn(group, get_user_model().objects.get(id=user1.id).groups.all())

        # POST to that page by username
        response = self.client.post(reverse("eighth_admin_add_member_to_group", kwargs={"group_id": group.id}), data={"query": "2021ttest"})
        self.assertEqual(200, response.status_code)
        self.assertIn(user1, response.context["users"])

        # Remove the user from the group and try with Ion user IDs
        user1 = get_user_model().objects.get(id=user1.id)
        user1.groups.remove(group)
        user1.save()

        response = self.client.post(reverse("eighth_admin_add_member_to_group", kwargs={"group_id": group.id}), data={"user_id": [user1.id]})
        self.assertEqual(302, response.status_code)
        self.assertIn(group, get_user_model().objects.get(id=user1.id).groups.all())

        # GET should not work
        response = self.client.get(reverse("eighth_admin_add_member_to_group", kwargs={"group_id": group.id}), data={"query": "2021ttest"})
        self.assertEqual(405, response.status_code)

    def test_remove_member_from_group_view(self):
        """Tests :func:`~intranet.apps.eighth.views.admin.groups.remove_member_from_group_view`"""

        self.make_admin()

        # Add a group and a user in that group
        group = Group.objects.get_or_create(name="test group 9")[0]
        user1 = get_user_model().objects.get_or_create(
            username="2021ttest",
            first_name="Tommy",
            last_name="Test",
            student_id=1234568,
            user_type="student",
            graduation_year=get_senior_graduation_year(),
        )[0]
        user1.groups.add(group)
        user1.save()

        # A GET should not do anything
        response = self.client.get(reverse("eighth_admin_remove_member_from_group", kwargs={"group_id": group.id, "user_id": user1.id}))
        self.assertEqual(405, response.status_code)
        self.assertIn(group, get_user_model().objects.get(id=user1.id).groups.all())

        # POST to remove the user from the group
        response = self.client.post(reverse("eighth_admin_remove_member_from_group", kwargs={"group_id": group.id, "user_id": user1.id}))
        self.assertEqual(302, response.status_code)
        self.assertNotIn(group, get_user_model().objects.get(id=user1.id).groups.all())
