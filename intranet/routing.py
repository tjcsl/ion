"""
Defines routes for channels
https://channels.readthedocs.io/en/latest/topics/routing.html
"""

from django.conf.urls import url

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from .apps.bus.consumers import BusConsumer

application = ProtocolTypeRouter({"websocket": AuthMiddlewareStack(URLRouter([url(r"^bus/$", BusConsumer)]))})
