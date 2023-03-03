import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from django.conf import settings
from django.utils import timezone

from .models import BusAnnouncement, Route

logger = logging.getLogger(__name__)


class BusConsumer(JsonWebsocketConsumer):
    groups = ["bus"]

    def connect(self):
        self.user = self.scope["user"]
        headers = dict(self.scope["headers"])
        remote_addr = headers[b"x-real-ip"].decode() if b"x-real-ip" in headers else self.scope["client"][0]
        if (not self.user.is_authenticated or self.user.is_restricted) and remote_addr not in settings.INTERNAL_IPS:
            self.connected = False
            self.close()
            return

        self.connected = True
        data = self._serialize(user=self.user)
        self.accept()
        self.send_json(data)

    def receive_json(self, content):  # pylint: disable=arguments-differ
        if not self.connected:
            return

        if content.get("type") == "keepalive":
            self.send_json({"type": "keepalive-response"})
            return

        if self.user is not None and self.user.is_authenticated and self.user.is_bus_admin:
            try:
                if self.within_time_range(content["time"]):
                    if content.get("announcement") or content.get("announcement") == "":
                        if content["announcement"].strip() == "":
                            content["announcement"] = ""
                        announcement = BusAnnouncement.object()
                        announcement.message = content["announcement"]
                        announcement.save()
                    else:
                        route = Route.objects.get(id=content["id"])
                        route.status = content["status"]
                        if content["time"] == "afternoon" and route.status == "a":
                            route.space = content["space"]
                        else:
                            route.space = ""
                        route.save()
                data = self._serialize()
                async_to_sync(self.channel_layer.group_send)("bus", {"type": "bus.update", "data": data})
            except Exception as e:
                logger.error(e)
                self.send_json({"error": "An error occurred."})
        else:
            self.send_json({"error": "User does not have permissions."})

    def bus_update(self, event):
        if not self.connected:
            return

        self.send_json(event["data"])

    def _serialize(self, user=None):
        all_routes = Route.objects.all()
        data = {}
        route_list = []
        for route in all_routes:
            serialized = {
                "id": route.id,
                "bus_number": route.bus_number,
                "space": route.space,
                "route_name": route.route_name,
                "status": route.status,
            }
            route_list.append(serialized)
            if user and user in route.user_set.all():
                data["userRouteId"] = route.id
                data["userRouteName"] = route.route_name

        data["allRoutes"] = route_list
        data["announcement"] = str(BusAnnouncement.object().message)

        return data

    def within_time_range(self, time):
        now_hour = timezone.localtime().hour
        within_morning = now_hour < settings.BUS_PAGE_CHANGEOVER_HOUR and time == "morning"
        within_afternoon = now_hour >= settings.BUS_PAGE_CHANGEOVER_HOUR and time == "afternoon"
        return within_morning or within_afternoon
