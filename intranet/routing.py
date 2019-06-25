"""
Defines routes for channels
https://channels.readthedocs.io/en/latest/topics/routing.html
"""
from channels.routing import route_class
from .apps.bus.consumers import BusConsumer

channel_routing = [route_class(BusConsumer, path=r"^/bus/")]
