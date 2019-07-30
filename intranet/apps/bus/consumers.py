from channels.generic.websocket import JsonWebsocketConsumer

from .models import Route


class BusConsumer(JsonWebsocketConsumer):
    groups = ["bus"]

    def connect(self):
        user = self.scope["user"]
        data = self._serialize(user=user)
        self.accept()
        self.send_json(data)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        if text_data:
            content = self.decode_json(text_data)
        else:
            self.send({"error": "Invalid data."})
            self.close()

        if self.scope["user"].has_admin_permission("bus"):
            try:
                route = Route.objects.get(id=content["id"])
                route.status = content["status"]
                if route.status == "a":
                    route.space = content["space"]
                else:
                    route.space = ""
                route.save()
                data = self._serialize()
                self.send_json(data)
            except Exception as e:
                # TODO: Add logging
                print(e)
                self.send({"error": "An error occurred."})
        else:
            self.send({"error": "User does not have permissions."})

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

        data["allRoutes"] = route_list
        return data
