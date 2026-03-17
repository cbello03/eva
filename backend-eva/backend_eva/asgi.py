"""
ASGI config for EVA Learning Platform.

Wraps the Django ASGI application with Django Channels routing.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_eva.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # WebSocket routes will be added here as apps are created
        # "websocket": AuthMiddlewareStack(URLRouter([...])),
    }
)
