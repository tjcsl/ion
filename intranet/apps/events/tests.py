from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ...test.ion_test import IonTestCase
from .models import Event, EventUserMap


class EventsTest(IonTestCase):
    """Tests for the events module."""

    def create_random_event(self, user, approved=False, time=timezone.now(), show_attending=True):
        event = Event.objects.create(title="Test Event", description="", time=time, location="TJHSST", user=user)
        if approved:
            event.approved = True
            event.approved_by = user
            event.rejected = False
        if not show_attending:
            event.show_attending = False
        event.save()
        return event

    def test_event_model(self):
        user = self.login()
        event = self.create_random_event(user)

        # Check event properties
        self.assertTrue(event.is_this_year)
        self.assertEqual(event.dashboard_type, "event")
        self.assertFalse(event.pinned)

        # Test creating/fetching EventUserMap
        self.assertFalse(EventUserMap.objects.exists())
        user_map = event.user_map
        # Test that EventUserMap was created
        self.assertTrue(EventUserMap.objects.filter(event=event).count(), 1)
        self.assertEqual(event.user_map, user_map)

        self.assertEqual(str(event.user_map), "UserMap: {}".format(event.title))

        self.assertEqual("UNAPPROVED - {} - {}".format(event.title, event.time), str(event))

        event = self.create_random_event(user, approved=True)
        self.assertEqual("{} - {}".format(event.title, event.time), str(event))

        next_event = self.create_random_event(user, time=timezone.now() + timezone.timedelta(days=15))
        prev_event = self.create_random_event(user, time=timezone.now() - timezone.timedelta(days=15))
        self.assertEqual(next_event.show_fuzzy_date(), False)
        self.assertEqual(prev_event.show_fuzzy_date(), False)

        next_event = self.create_random_event(user, time=timezone.now() + timezone.timedelta(days=1))
        prev_event = self.create_random_event(user, time=timezone.now() - timezone.timedelta(days=1))
        self.assertEqual(next_event.show_fuzzy_date(), True)
        self.assertEqual(prev_event.show_fuzzy_date(), True)

    def test_events_root_non_admin(self):
        _ = self.login()

        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)

        self.assertFalse(response.context["is_events_admin"])

    def test_join_event(self):
        user = self.login()
        event = self.create_random_event(user)

        # Test GET of valid event
        response = self.client.get(reverse("join_event", args=[event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], event)
        self.assertEqual(response.context["is_events_admin"], False)

        # Test GET of nonexistent event
        response = self.client.get(reverse("join_event", args=[9999]))
        self.assertEqual(response.status_code, 404)

        # Test marking as attending
        data = {"attending": "true"}
        response = self.client.post(reverse("join_event", args=[event.id]), data=data, follow=True)
        self.assertRedirects(response, reverse("events"))
        self.assertEqual(event.attending.count(), 1)

        # Test marking as not attending
        data = {"attending": "false"}
        response = self.client.post(reverse("join_event", args=[event.id]), data=data)
        self.assertRedirects(response, reverse("events"))
        self.assertFalse(event.attending.exists())

        # Test redirect when not showing attending users
        event.show_attending = False
        event.save()
        response = self.client.get(reverse("join_event", args=[event.id]))
        self.assertRedirects(response, reverse("events"))
        response = self.client.post(reverse("join_event", args=[event.id]), data=data)
        self.assertRedirects(response, reverse("events"))

    def test_view_roster(self):
        # Test as a regular person
        user = self.login()

        event = self.create_random_event(user)

        # Test with non-existent event
        response = self.client.get(reverse("event_roster", args=[9999]))
        self.assertEqual(response.status_code, 404)

        # Test with no attendees
        response = self.client.get(reverse("event_roster", args=[event.id]))
        expected_context = {"event": event, "viewable_roster": [], "num_hidden_members": 0, "is_events_admin": False}
        for key in expected_context:
            self.assertEqual(response.context[key], expected_context[key])
        self.assertQuerysetEqual(response.context["full_roster"], get_user_model().objects.none())

        # Test with a few attendees
        num_users = 5
        for i in range(num_users):
            user = get_user_model().objects.create(username="2020jdoe{}".format(i))
            event.attending.add(user)
        event.save()

        response = self.client.get(reverse("event_roster", args=[event.id]))
        self.assertEqual(response.context["full_roster"].count(), num_users)

        # Since no one shows their eighth period activities and the user
        # is not an administrator, no users are viewable.
        self.assertEqual(response.context["viewable_roster"], [])

    def test_add_event(self):
        _ = self.make_admin()

        # Test GET of valid event id
        response = self.client.get(reverse("add_event"))
        expected_context = {"action": "add", "action_title": "Add", "is_events_admin": True}
        for key in expected_context:
            self.assertEqual(response.context[key], expected_context[key])

        # Test POST of valid form
        data = {
            "title": "Title",
            "description": "Description",
            "time": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": "Location",
            "scheduled_activity": "",
            "announcement": "",
            "groups": 1,
            "show_attending": "on",
            "show_on_dashboard": "on",
            "category": "sports",
            "open_to": "students",
        }
        response = self.client.post(reverse("add_event"), data=data, follow=True)

        messages = list(response.context.get("messages"))
        success_message = "Because you are an administrator, this event was auto-approved."
        self.assertEqual(messages[0].message, success_message)
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        self.assertEqual(event.title, data["title"])
        self.assertEqual(event.description, data["description"])
        self.assertEqual(event.location, data["location"])

    def test_request_event(self):
        _ = self.login()

        self.assertFalse(Event.objects.exists())

        # Test GET context
        response = self.client.get(reverse("request_event"))
        expected_context = {"action": "request", "action_title": "Submit", "is_events_admin": False}
        for key in expected_context:
            self.assertEqual(response.context[key], expected_context[key])

        # Test POST of valid form
        data = {
            "title": "Title",
            "description": "Description",
            "time": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": "Location",
            "groups": [],
            "show_attending": "on",
            "show_on_dashboard": "on",
            "category": "sports",
            "open_to": "students",
        }

        response = self.client.post(reverse("request_event"), data=data, follow=True)
        success_message = "Your event needs to be approved by an administrator. If approved, it should appear on Intranet within 24 hours."

        self.assertEqual(response.status_code, 200)
        messages = list(response.context.get("messages"))
        self.assertEqual(messages[0].message, success_message)
        self.assertEqual(Event.objects.count(), 1)
        self.assertFalse(Event.objects.first().approved)

    def test_modify_event(self):
        user = self.login()

        event = self.create_random_event(user)

        # Permission should be denied to non-event admins
        response = self.client.get(reverse("modify_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        # Permission should be denied to non-event admins
        response = self.client.post(reverse("modify_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        user = self.make_admin()

        # Test nonexistent event ids
        response = self.client.get(reverse("modify_event", args=[9999]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("modify_event", args=[9999]))
        self.assertEqual(response.status_code, 404)

        # Test GET of valid event id
        response = self.client.get(reverse("modify_event", args=[event.id]))
        expected_context = {"action": "modify", "action_title": "Modify", "id": str(event.id), "is_events_admin": True}
        for key in expected_context:
            self.assertEqual(response.context[key], expected_context[key])

        # Test POST of valid form
        data = {
            "title": "New title",
            "description": "New description",
            "time": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": "New location",
            "scheduled_activity": "",
            "announcement": "",
            "groups": 1,
            "show_attending": "on",
            "show_on_dashboard": "on",
            "category": "sports",
            "open_to": "students",
        }
        response = self.client.post(reverse("modify_event", args=[event.id]), data=data, follow=True)

        messages = list(response.context.get("messages"))
        self.assertEqual(messages[0].message, "Successfully modified event.")
        event = Event.objects.get(id=event.id)
        self.assertEqual(event.title, data["title"])
        self.assertEqual(event.description, data["description"])
        self.assertEqual(event.location, data["location"])

    def test_delete_event(self):
        user = self.login()

        event = self.create_random_event(user)

        # Permission should be denied to non-event admins
        response = self.client.get(reverse("delete_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        # Permission should be denied to non-event admins
        response = self.client.post(reverse("delete_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        user = self.make_admin()

        # Test GET for valid event
        response = self.client.get(reverse("delete_event", args=[event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], event)
        self.assertEqual(response.context["action"], "delete")

        # Test GET for nonexistent event
        response = self.client.get(reverse("delete_event", args=[9999]))
        self.assertEqual(response.status_code, 404)

        # Test POST for nonexistent event id
        response = self.client.post(reverse("delete_event", args=[9999]))
        self.assertEqual(response.status_code, 404)

        # Test deletion
        response = self.client.post(reverse("delete_event", args=[event.id]))
        self.assertRedirects(response, reverse("events"))
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_show_hide_event_no_auth(self):
        # Test reauthentication for showing event
        response = self.client.post(reverse("show_event"), follow=True)
        self.assertRedirects(response, reverse("login") + "?next={}".format(reverse("show_event")))

        # Test reauthentication for hiding event
        response = self.client.post(reverse("hide_event"), follow=True)
        self.assertRedirects(response, reverse("login") + "?next={}".format(reverse("hide_event")))

    def test_show_hide_event(self):
        user = self.login()

        event = self.create_random_event(user)

        # Test disallowed method for hide event
        response = self.client.get(reverse("hide_event"))
        self.assertEqual(response.status_code, 405)

        # Test POST with no event_id for hide event
        response = self.client.post(reverse("hide_event"))
        self.assertEqual(response.status_code, 404)

        # Test POST with malformed event_id for hide event
        response = self.client.post(reverse("hide_event"), data={"event_id": "bad"})
        self.assertEqual(response.status_code, 404)

        # Test hiding event
        response = self.client.post(reverse("hide_event"), data={"event_id": event.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Hidden")
        user_map = EventUserMap.objects.get(event=event)
        self.assertTrue(user in user_map.users_hidden.all())

        # Test for disallowed method for show event
        response = self.client.get(reverse("show_event"))
        self.assertEqual(response.status_code, 405)

        # Test POST with no event_id for show event
        response = self.client.post(reverse("show_event"))
        self.assertEqual(response.status_code, 404)

        # Test POST with malformed event_id for hide event
        response = self.client.post(reverse("hide_event"), data={"event_id": "bad"})
        self.assertEqual(response.status_code, 404)

        # Test showing event
        response = self.client.post(reverse("show_event"), data={"event_id": event.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Unhidden")
        self.assertFalse(user in user_map.users_hidden.all())
