import random
from channels.generic.websockets import JsonWebsocketConsumer

from .models import Route


class BusConsumer(JsonWebsocketConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return ["bus"]

    def connect(self, message):
        print("connected")
        print(message.user)
        if not message.user.is_authenticated:
            self.close()
            return
        data = self._serialize(user=message.user)
        self.send(data)

    def receive(self, content):
        print("received message")
        if (self.message.user.has_admin_permission('bus')):
            try:
                route = Route.objects.get(id=content['id'])
                route.status = content['status']
                if route.status == 'a':
                    route.space = content['space']
                else:
                    route.space = ''
                route.save()
                data = self._serialize()
                self.group_send('bus', data)
            except Exception as e:
                # TODO: Add logging
                print(e)
                self.send({'error': 'An error occurred.'})

    def _serialize(self, user=None):
        print(user)
        all_routes = Route.objects.all()
        data = {}
        route_list = []
        for route in all_routes:
            serialized = {
                'id': route.id,
                'bus_number': route.bus_number,
                'space': route.space,
                'route_name': route.route_name,
                'status': route.status,
            }
            route_list.append(serialized)
            if user and user in route.user_set.all():
                data['userRouteId'] = route.id
        data['allRoutes'] = route_list
        return data
