import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from ...utils.date import get_senior_graduation_year
from ..users.models import Group
from .models import Announcement, AnnouncementRequest


class AnnouncementTest(IonTestCase):

    """Tests for the announcements module."""

    def setUp(self):
        self.user = get_user_model().objects.get_or_create(
            username="awilliam", graduation_year=get_senior_graduation_year() + 1, user_type="student"
        )[0]

    def test_get_announcements(self):
        self.login()

        response = self.client.get(reverse("view_announcements"))
        self.assertEqual(response.status_code, 200)

        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test8", content="test8")[0]
        response = self.client.get(reverse("view_announcements"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(announce.content, response.content.decode("UTF-8"))

        response = self.client.get(reverse("view_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)

    def test_change_announcements(self):
        self.login()
        group = Group.objects.get_or_create(name="admin_all")[0]
        get_user_model().objects.get_or_create(username="awilliam")[0].groups.add(group)

        response = self.client.get(reverse("add_announcement"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin_approve_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("approve_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("announcements_archive"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("delete_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("hide_announcement"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("modify_announcement", args=[9001]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("request_announcement"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("show_announcement"))
        self.assertEqual(response.status_code, 404)

    def test_announcement_approval_allowed_users(self):
        """Tests to ensure that only allowed users can approve announcements."""
        teacher = get_user_model().objects.get_or_create(username="teacher", user_type="teacher", first_name="timmy", last_name="teacher")[0]
        counselor = get_user_model().objects.get_or_create(username="counselor", user_type="counselor", first_name="c", last_name="c")[0]
        user = get_user_model().objects.get_or_create(username="user", user_type="user", first_name="ursula", last_name="user")[0]
        student = get_user_model().objects.get_or_create(username="3000student", user_type="student", first_name="s", last_name="tudent")[0]
        self.assertEqual(list(get_user_model().objects.get_approve_announcements_users_sorted()), [counselor, teacher, user])
        self.assertNotIn(student, get_user_model().objects.get_approve_announcements_users_sorted())

    def test_announcement_request(self):
        """Tests the announcement request view."""
        self.login()
        response = self.client.get(reverse("request_announcement"))
        self.assertEqual(response.status_code, 200)

        teacher = get_user_model().objects.get_or_create(username="awilliam1", user_type="teacher", first_name="a", last_name="william")[0]

        # Now, try to POST an announcement
        response = self.client.post(
            reverse("request_announcement"),
            data={
                "title": "This is a test!",
                "author": "Sysadmins",
                "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "expiration_date": "3000-01-01 00:00:00",
                "teachers_requested": str(teacher.id),
                "notes": "Enter something here!",
            },
        )

        self.assertEqual(response.status_code, 302)  # to "success" page

        self.assertEqual(1, AnnouncementRequest.objects.count())

        # See if that AnnouncementRequest appears
        self.assertEqual(
            AnnouncementRequest.objects.filter(
                title="This is a test!",
                author="Sysadmins",
                content="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                teachers_requested=teacher,
                notes="Enter something here!",
            ).count(),
            1,
        )

    def test_request_announcement_success_view(self):
        self.login()
        response = self.client.get(reverse("request_announcement_success"))
        self.assertEqual(200, response.status_code)

    def test_request_announcement_success_self_view(self):
        self.login()
        response = self.client.get(reverse("request_announcement_success_self"))
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["self"])

    def test_approve_announcement_view(self):
        teacher = get_user_model().objects.get_or_create(username="awilliam1", user_type="teacher", first_name="a", last_name="william")[0]
        user = self.login()
        request = AnnouncementRequest.objects.create(title="test", content="hello", author="Sysadmins", user=user)

        self.login("awilliam1")

        # The user is not in the "requested_teachers" list, so this should 302 to the index page
        response = self.client.get(reverse("approve_announcement", kwargs={"req_id": request.id}))
        self.assertEqual(302, response.status_code)

        response = self.client.get(reverse("approve_announcement", kwargs={"req_id": request.id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("You do not have permission to approve this announcement.", list(map(str, list(response.context["messages"]))))

        request.teachers_requested.add(teacher)
        request.save()

        # This should now just 200
        response = self.client.get(reverse("approve_announcement", kwargs={"req_id": request.id}))
        self.assertEqual(200, response.status_code)
        self.assertNotIn("You do not have permission to approve this announcement.", list(map(str, list(response.context["messages"]))))

        # Don't approve this announcement
        response = self.client.post(
            reverse("approve_announcement", kwargs={"req_id": request.id}),
            data={
                "title": "test",
                "content": "hello",
                "author": "test sysadmins",
                "expiration_date": "3000-01-01",
                "user": request.user.id,
                "teachers_requested": teacher.id,
                "reject": "Reject Announcement",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("reject", response.context.get("status"))

        # Now, approve this announcement
        response = self.client.post(
            reverse("approve_announcement", kwargs={"req_id": request.id}),
            data={
                "title": "test",
                "content": "hello",
                "author": "test sysadmins",
                "user": request.user.id,
                "teachers_requested": teacher.id,
                "approve": "approve",
                "notify_post": "1",
                "expiration_date": "3000-01-01",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("accept", response.context.get("status"))

        self.assertEqual(1, AnnouncementRequest.objects.filter(title="test", content="hello", teachers_approved=teacher).count())

    def test_admin_approve_announcement_view(self):
        teacher = get_user_model().objects.get_or_create(username="awilliam1", user_type="teacher", first_name="a", last_name="william")[0]
        user = self.make_admin()

        # Create an AnnouncementRequest.
        announce_request = AnnouncementRequest.objects.get_or_create(title="test", content="hello", user=user)[0]
        announce_request.teachers_requested.add(teacher)
        announce_request.save()

        # Load the page.
        response = self.client.get(reverse("admin_approve_announcement", kwargs={"req_id": announce_request.id}))
        self.assertEqual(200, response.status_code)

        # Reject the announcement.
        response = self.client.post(
            reverse("admin_approve_announcement", kwargs={"req_id": announce_request.id}),
            data={
                "title": "test",
                "content": "hello",
                "author": "test sysadmins",
                "user": announce_request.user.id,
                "teachers_requested": teacher.id,
                "expiration_date": "3000-01-01",
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(AnnouncementRequest.objects.get(title="test", content="hello").rejected)

        # Accept the announcement now
        response = self.client.post(
            reverse("admin_approve_announcement", kwargs={"req_id": announce_request.id}),
            data={
                "title": "test",
                "content": "hello",
                "author": "test sysadmins",
                "user": announce_request.user.id,
                "teachers_requested": teacher.id,
                "expiration_date": "3000-01-01",
                "approve": "approve",
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Announcement.objects.filter(title="test", content="hello").count())

        # Do another announcement, but restrict posting to a group this time
        group = Group.objects.create(name="test_group")
        user.groups.add(group)
        user.save()

        announce_request2 = AnnouncementRequest.objects.get_or_create(title="test", content="hello", user=user)[0]
        announce_request2.teachers_requested.add(teacher)
        announce_request2.save()

        response = self.client.post(
            reverse("admin_approve_announcement", kwargs={"req_id": announce_request2.id}),
            data={
                "title": "test2",
                "content": "hello",
                "author": "test sysadmins",
                "user": announce_request2.user.id,
                "teachers_requested": teacher.id,
                "expiration_date": "3000-01-01",
                "approve": "approve",
                "groups": group.id,
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Announcement.objects.filter(title="test2", content="hello", groups=group).count())

    def test_admin_request_status_view(self):
        # Delete all the AnnouncementRequests to ensure that nothing interferes with this
        AnnouncementRequest.objects.all().delete()

        user = self.make_admin()

        # Load the page.
        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.context["awaiting_teacher"]))
        self.assertEqual(0, len(response.context["awaiting_approval"]))
        self.assertEqual(0, len(response.context["approved"]))
        self.assertEqual(0, len(response.context["rejected"]))

        # Add an AnnouncementRequest
        announce_request = AnnouncementRequest.objects.get_or_create(title="test", content="hello")[0]
        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context["awaiting_teacher"]))
        self.assertEqual(0, len(response.context["awaiting_approval"]))
        self.assertEqual(0, len(response.context["approved"]))
        self.assertEqual(0, len(response.context["rejected"]))

        # "Approve" the announcement
        announce_request.teachers_approved.add(user)
        announce_request.save()

        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.context["awaiting_teacher"]))
        self.assertEqual(1, len(response.context["awaiting_approval"]))
        self.assertEqual(0, len(response.context["approved"]))
        self.assertEqual(0, len(response.context["rejected"]))

        # Reject the announcement
        announce_request.rejected = True
        announce_request.save()

        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.context["awaiting_teacher"]))
        self.assertEqual(0, len(response.context["awaiting_approval"]))
        self.assertEqual(0, len(response.context["approved"]))
        self.assertEqual(1, len(response.context["rejected"]))

        # Post the announcement
        announce = Announcement.objects.get_or_create(title="test", content="hello")[0]
        announce_request.posted = announce
        announce_request.rejected = False
        announce_request.save()

        response = self.client.get(reverse("admin_request_status"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.context["awaiting_teacher"]))
        self.assertEqual(0, len(response.context["awaiting_approval"]))
        self.assertEqual(1, len(response.context["approved"]))
        self.assertEqual(0, len(response.context["rejected"]))

    def test_add_announcement_view(self):
        self.make_admin()

        # Load the add page
        response = self.client.get(reverse("add_announcement"))
        self.assertEqual(200, response.status_code)

        # Post an announcement
        response = self.client.post(
            reverse("add_announcement"),
            data={
                "title": "test3",
                "content": "hello3",
                "author": "test sysadmins",
                "expiration_date": "3000-01-01",
                "notify_post": True,
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Announcement.objects.filter(title="test3", content="hello3").count())

        # Do it again, but check the "notify all" box
        response = self.client.post(
            reverse("add_announcement"),
            data={
                "title": "test4",
                "content": "hello3",
                "author": "test sysadmins",
                "expiration_date": "3000-01-01",
                "notify_post": True,
                "notify_email_all": True,
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Announcement.objects.filter(title="test4", content="hello3").count())

    def test_view_announcement_view(self):
        self.login()

        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test4", content="test4")[0]

        # Load the page
        response = self.client.get(reverse("view_announcement", kwargs={"announcement_id": announce.id}))
        self.assertEqual(200, response.status_code)
        self.assertIn("test4", response.content.decode("UTF-8"))

    def test_modify_announcement_view(self):
        self.make_admin()

        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test5", content="test5")[0]

        # Load the page
        response = self.client.get(reverse("modify_announcement", kwargs={"announcement_id": announce.id}))
        self.assertEqual(200, response.status_code)
        self.assertIn("test5", response.content.decode("UTF-8"))

        # Modify the announcement
        response = self.client.post(
            reverse("modify_announcement", kwargs={"announcement_id": announce.id}),
            data={
                "title": "test5-1",
                "content": "hello3there",
                "author": "test sysadmins2",
                "expiration_date": "3000-01-01",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Announcement.objects.filter(title="test5-1", content="hello3there", author="test sysadmins2", id=announce.id).count())

    def test_delete_announcement_view(self):
        self.make_admin()

        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test6", content="test6")[0]

        # Load the page
        response = self.client.get(reverse("delete_announcement", kwargs={"announcement_id": announce.id}))
        self.assertEqual(200, response.status_code)
        self.assertEqual(announce, response.context["announcement"])

        # Test expiring the announcement
        response = self.client.post(reverse("delete_announcement", kwargs={"announcement_id": announce.id}), data={"id": announce.id}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertLess(Announcement.objects.get(id=announce.id).expiration_date, timezone.localtime())

        # Test a full delete
        response = self.client.post(
            reverse("delete_announcement", kwargs={"announcement_id": announce.id}), data={"id": announce.id, "full_delete": True}, follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, Announcement.objects.filter(id=announce.id).count())

    def test_show_announcement_view(self):
        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test7", content="test7")[0]

        # Hide that announcement
        user = self.login()
        announce.user_map.users_hidden.add(user)
        announce.user_map.save()

        # Sanity check
        assert announce in Announcement.objects.hidden_announcements(user)

        # Show that announcement again
        response = self.client.post(reverse("show_announcement"), data={"announcement_id": announce.id})
        self.assertEqual(200, response.status_code)

        self.assertNotIn(announce, Announcement.objects.hidden_announcements(user))

        # Check that GET returns 405
        response = self.client.get(reverse("show_announcement"))
        self.assertEqual(405, response.status_code)

    def test_hide_announcement_view(self):
        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test8", content="test8")[0]

        # Hide that announcement
        user = self.login()
        response = self.client.post(reverse("hide_announcement"), data={"announcement_id": announce.id})
        self.assertEqual(200, response.status_code)

        self.assertIn(announce, Announcement.objects.hidden_announcements(user))

        # Check that GET returns 405
        response = self.client.get(reverse("hide_announcement"))
        self.assertEqual(405, response.status_code)


class ApiTest(IonTestCase):
    def test_api_announcements_list(self):
        # First, just test loading an empty list
        self.login()
        response = self.client.get(reverse("api_announcements_list_create"), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_json = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(0, len(response_json["results"]))

        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test9", content="test9")[0]

        response = self.client.get(reverse("api_announcements_list_create"), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_json = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(1, len(response_json["results"]))
        self.assertEqual(announce.title, response_json["results"][0]["title"])

    def test_api_announcements_detail(self):
        self.login()

        # Add an announcement
        announce = Announcement.objects.get_or_create(title="test9", content="test9")[0]

        response = self.client.get(reverse("api_announcements_detail", kwargs={"pk": announce.id}), data={"format": "json"})
        self.assertEqual(200, response.status_code)

        response_json = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(announce.title, response_json["title"])
