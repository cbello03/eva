"""
ASGI config for EVA Learning Platform.

Wraps the Django ASGI application with Django Channels routing
for WebSocket support (chat, notifications, collaboration).
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_eva.settings")

django_asgi_app = get_asgi_application()

from apps.social.consumers import ChatConsumer  # noqa: E402
from apps.collaboration.consumers import CollabConsumer  # noqa: E402
from apps.notifications.consumers import NotificationConsumer  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(
            [
                path("ws/chat/<int:course_id>/", ChatConsumer.as_asgi()),
                path(
                    "ws/collab/<int:exercise_id>/<int:group_id>/",
                    CollabConsumer.as_asgi(),
                ),
                path("ws/notifications/", NotificationConsumer.as_asgi()),
            ]
        ),
    }
)
