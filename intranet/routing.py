"""
Defines routes for channels
https://channels.readthedocs.io/en/latest/topics/routing.html
"""
from typing import Optional

from channels.auth import AuthMiddlewareStack
from channels.generic.websocket import WebsocketConsumer
from channels.routing import ProtocolTypeRouter, URLRouter

from django.urls import re_path

from .apps.bus.consumers import BusConsumer
from .apps.signage.consumers import SignageConsumer


class WebsocketCloseConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.close()

    def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None):
        pass

    def disconnect(self, code):
        pass


application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    re_path(r"^bus/$", BusConsumer),
                    # This MUST match the signage_display entry in intranet/apps/signage/urls.py
                    re_path(r"^signage/display/(?P<display_name>[-_\w]+)?$", SignageConsumer),
                    re_path(r"^.*$", WebsocketCloseConsumer),
                ]
            )
        )
    }
)
