from channels.generic.websocket import JsonWebsocketConsumer

from django.conf import settings
from django.utils import timezone

from .models import Sign


class SignageConsumer(JsonWebsocketConsumer):
    def connect(self) -> None:
        self.user = self.scope["user"]
        headers = dict(self.scope["headers"])
        remote_addr = headers[b"x-real-ip"].decode() if b"x-real-ip" in headers else self.scope["client"][0]
        if not self.user.is_authenticated and remote_addr not in settings.INTERNAL_IPS:
            self.connected = False
            self.close()
            return

        self.display_name = self.scope["url_route"]["kwargs"].get("display_name", "")

        try:
            self.sign_obj = Sign.objects.get(display=self.display_name)
        except Sign.DoesNotExist:
            self.connected = False
            self.close()
            return

        self.connected = True
        self.accept()

        self.sign_obj.latest_heartbeat_time = timezone.localtime()
        self.sign_obj.save(update_fields=["latest_heartbeat_time"])

    def receive_json(self, content) -> None:  # pylint: disable=arguments-differ
        if not self.connected:
            return

        if self.sign_obj is not None:
            self.sign_obj.refresh_from_db()
            self.sign_obj.latest_heartbeat_time = timezone.localtime()
            self.sign_obj.save(update_fields=["latest_heartbeat_time"])

        if content.get("type") == "heartbeat":
            self.send_json({"type": "heartbeat-response"})
            return

    def disconnect(self, code: int) -> None:
        # We want to check because the connection may have been rejected at the start
        # and later on we assume it was not.
        if not self.connected:
            return

        self.connnected = False

        if self.sign_obj is not None:
            self.sign_obj.refresh_from_db()
            self.sign_obj.latest_heartbeat_time = None
            self.sign_obj.save(update_fields=["latest_heartbeat_time"])
