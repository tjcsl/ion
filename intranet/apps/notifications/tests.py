# pylint: disable=no-member,unused-argument

from unittest import mock
from unittest.mock import ANY

from django.urls import reverse
from push_notifications.models import WebPushDevice
from rest_framework.response import Response

from intranet.apps.notifications.models import WebPushNotification
from intranet.apps.notifications.tasks import send_bulk_notification, send_notification_to_device, send_notification_to_user
from intranet.test.ion_test import IonTestCase


class NotificationsWebpushTest(IonTestCase):
    """Tests for the notifications/webpush module, including api"""

    def setUp(self):
        self.endpoint = "push.api.example.com/example/endpoint/id"
        self.mock_device = mock.Mock()
        self.mock_device.registration_id = self.endpoint
        self.mock_device.auth = "authtest"
        self.mock_device.p256dh = "p256dhtest"
        self.user = self.login()

    def create_webpush_device(self, user, registration_id):
        return WebPushDevice.objects.create(
            registration_id=registration_id,
            p256dh=self.mock_device.p256dh,
            auth=self.mock_device.auth,
            user=user,
        )

    @mock.patch("intranet.apps.notifications.api.GetApplicationServerKey.get")
    def test_get_app_server_key(self, mock_view):
        mock_view.return_value = Response({"applicationServerKey": "mock-key"}, status=200)

        response = self.client.get(reverse("api_get_vapid_application_server_key"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("applicationServerKey", response.json())

    def test_webpush_subscription(self):
        response = self.client.post(
            reverse("api_webpush_subscribe"),
            format="json",
            data={
                "registration_id": self.mock_device.registration_id,
                "p256dh": self.mock_device.p256dh,
                "auth": self.mock_device.auth,
            },
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(WebPushDevice.objects.count(), 1)
        obj = WebPushDevice.objects.get(registration_id=self.mock_device.registration_id)
        self.assertEqual(obj.user, self.user)

    def test_webpush_unsubscribe(self):
        self.create_webpush_device(self.user, self.mock_device.registration_id)

        self.assertEqual(WebPushDevice.objects.count(), 1)

        response = self.client.post(
            reverse("api_webpush_unsubscribe"),
            format="json",
            data={
                "endpoint": self.mock_device.registration_id,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(WebPushDevice.objects.count(), 0)

    def test_webpush_update_subscription(self):
        self.create_webpush_device(self.user, self.mock_device.registration_id)

        new_registration_id = "push.api.example.com/new/unique/id"
        new_p256dh = "p256dhalt"
        new_auth = "authalt"

        response = self.client.post(
            reverse("api_webpush_update_subscription"),
            format="json",
            data={
                "old_registration_id": self.mock_device.registration_id,
                "registration_id": new_registration_id,
                "p256dh": new_p256dh,
                "auth": new_auth,
            },
        )

        self.assertEqual(response.status_code, 200)

        device = WebPushDevice.objects.filter(user=self.user).first()

        self.assertEqual(device.registration_id, new_registration_id)
        self.assertEqual(device.p256dh, new_p256dh)
        self.assertEqual(device.auth, new_auth)

    def test_webpush_subscription_status(self):
        response = self.client.post(
            reverse("api_webpush_subscription_status"),
            format="json",
            data={
                "endpoint": self.mock_device.registration_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], False)

        response = self.client.post(
            reverse("api_webpush_subscribe"),
            format="json",
            data={
                "registration_id": self.mock_device.registration_id,
                "p256dh": self.mock_device.p256dh,
                "auth": self.mock_device.auth,
            },
        )

        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            reverse("api_webpush_subscription_status"),
            format="json",
            data={
                "endpoint": self.mock_device.registration_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], True)

    @mock.patch("push_notifications.models.WebPushDevice.send_message", autospec=True)
    def test_webpush_send_user_message(self, webpush_device_mock):
        device = self.create_webpush_device(self.user, self.mock_device.registration_id)

        title = "example"
        body = "notification"
        url = "example.com"

        send_notification_to_user(user=self.user, title=title, body=body, data={"url": url})

        WebPushDevice.send_message.assert_called_with(device, ANY)

        self.assertEqual(WebPushNotification.objects.count(), 1)

        notification = WebPushNotification.objects.first()
        self.assertEqual(notification.target, notification.Targets.USER)

    @mock.patch("push_notifications.models.WebPushDevice.send_message", autospec=True)
    def test_webpush_send_device_message(self, webpush_device_mock):
        device = self.create_webpush_device(self.user, self.mock_device.registration_id)

        title = "example"
        body = "notification"
        url = "example.com"

        device = WebPushDevice.objects.filter(user=self.user).first()

        send_notification_to_device(device=device, title=title, body=body, data={"url": url})

        WebPushDevice.send_message.assert_called_with(device, ANY)

        self.assertEqual(WebPushNotification.objects.count(), 1)

        notification = WebPushNotification.objects.first()
        self.assertEqual(notification.target, notification.Targets.DEVICE)

    @mock.patch("push_notifications.models.WebPushDevice.send_message", autospec=True)
    def test_webpush_send_bulk_message(self, webpush_device_mock):
        self.create_webpush_device(self.user, self.mock_device.registration_id)
        self.create_webpush_device(self.user, "push.api.example.com/unique/id")

        title = "example"
        body = "notification"
        url = "example.com"

        filtered_objects = WebPushDevice.objects.filter(user=self.user)

        send_bulk_notification(filtered_objects=filtered_objects, title=title, body=body, data={"url": url})

        WebPushDevice.send_message.assert_called_with(ANY, ANY)

        self.assertEqual(WebPushNotification.objects.count(), 1)

        notification = WebPushNotification.objects.first()
        self.assertEqual(notification.target, notification.Targets.DEVICE_QUERYSET)

    def test_webpush_notif_list_view(self):
        self.user = self.make_admin()
        response = self.client.get(reverse("notif_webpush_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notifications/webpush_list.html")

    def test_webpush_notif_device_info_view(self):
        self.user = self.make_admin()
        device = self.create_webpush_device(user=self.user, registration_id=self.mock_device.registration_id)

        WebPushNotification.objects.create(
            title="example",
            body="description",
            target=WebPushNotification.Targets.DEVICE,
            device_sent=device,
        )

        response = self.client.get(reverse("notif_webpush_device_view", kwargs={"model_id": WebPushNotification.objects.all().first().id}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notifications/webpush_device_info.html")

    @mock.patch("intranet.apps.notifications.tasks.send_bulk_notification.delay", autospec=True)
    def test_webpush_post_view(self, send_mock):
        self.user = self.make_admin()
        self.create_webpush_device(self.user, self.mock_device.registration_id)
        response = self.client.get(reverse("notif_webpush_post_view"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notifications/webpush_post.html")

        title = "example"
        body = "notification"
        url = "https://www.example.com"

        response = self.client.post(
            reverse("notif_webpush_post_view"),
            {
                "title": title,
                "body": body,
                "url": url,
            },
        )

        # We can't assert if send_mock was called with specific argument values...
        # because mock doesn't support comparing Django objects.
        # Instead, it changes the id of the object when mocking, meaning they can't be compared

        send_mock.assert_called_once_with(title=ANY, body=ANY, data=ANY, filtered_objects=ANY)
