from channels.routing import route_class
from .apps.bus.consumers import BusConsumer

channel_routing = [route_class(BusConsumer, path=r"^/bus/")]
