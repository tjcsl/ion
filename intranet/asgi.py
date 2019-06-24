import os
import channels.asgi

"""
Sets up application for channels
"""

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
channel_layer = channels.asgi.get_channel_layer()
