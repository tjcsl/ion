from django.urls import reverse
from django.utils import timezone

from .models import Event, EventUserMap
from ...test.ion_test import IonTestCase


class EventsTest(IonTestCase):
    """Tests for the events module."""

    def create_random_event(self, user):
        return Event.objects.create(title="Test Event", description="", time=timezone.now(), location="TJHSST", user=user)

    def test_events_root_non_admin(self):
        self.login()

        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)

        self.assertFalse(response.context["is_events_admin"])

    def test_modify_event(self):
        self.login()

        event = self.create_random_event(self.user)

        # Permission should be denied to non-event admins
        response = self.client.get(reverse("modify_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        # Permission should be denied to non-event admins
        response = self.client.post(reverse("modify_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        self.make_admin()

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
        self.login()

        event = self.create_random_event(self.user)

        # Permission should be denied to non-event admins
        response = self.client.get(reverse("delete_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        # Permission should be denied to non-event admins
        response = self.client.post(reverse("delete_event", args=[event.id]))
        self.assertEqual(response.status_code, 403)

        self.make_admin()

        # Test GET for valid event
        response = self.client.get(reverse("delete_event", args=[event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], event)

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
        self.login()

        event = self.create_random_event(self.user)

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
        self.assertTrue(self.user in user_map.users_hidden.all())

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
        self.assertFalse(self.user in user_map.users_hidden.all())
