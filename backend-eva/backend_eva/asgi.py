"""
ASGI config for EVA Learning Platform.

Wraps the Django ASGI application with Django Channels routing
for WebSocket support (chat, notifications, collaboration).

Includes a JWT authentication middleware that extracts the token from
the ``?token=<jwt>`` query parameter and populates ``scope["user"]``
so that individual consumers can rely on ``self.scope["user"]`` instead
of duplicating authentication logic.
"""

import os
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_eva.settings")

# This call triggers django.setup() — must happen before any model imports.
django_asgi_app = get_asgi_application()

from django.contrib.auth.models import AnonymousUser  # noqa: E402

from apps.accounts.models import User  # noqa: E402
from apps.accounts.services import JWT_ALGORITHM  # noqa: E402
from apps.collaboration.consumers import CollabConsumer  # noqa: E402
from apps.notifications.consumers import NotificationConsumer  # noqa: E402
from apps.social.consumers import ChatConsumer  # noqa: E402


# ---------------------------------------------------------------------------
# JWT Authentication Middleware for WebSocket connections
# ---------------------------------------------------------------------------


@database_sync_to_async
def _get_user_from_token(token: str) -> User | AnonymousUser:
    """Decode a JWT access token and return the corresponding User.

    Returns ``AnonymousUser`` when the token is missing, invalid, expired,
    or does not correspond to an existing user.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "role", "exp", "type"]},
        )
    except jwt.PyJWTError:
        return AnonymousUser()

    if payload.get("type") != "access":
        return AnonymousUser()

    try:
        return User.objects.get(pk=int(payload["sub"]))
    except (User.DoesNotExist, ValueError, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware:
    """ASGI middleware that authenticates WebSocket connections via JWT.

    Reads the ``token`` query parameter, validates it, and sets
    ``scope["user"]`` to the authenticated ``User`` instance (or
    ``AnonymousUser`` if authentication fails).  Individual consumers
    still decide whether to accept or reject the connection based on
    ``scope["user"]``.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        if token:
            scope["user"] = await _get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# WebSocket URL routes
# ---------------------------------------------------------------------------

websocket_urlpatterns = [
    path("ws/chat/<int:course_id>/", ChatConsumer.as_asgi()),
    path(
        "ws/collab/<int:exercise_id>/<int:group_id>/",
        CollabConsumer.as_asgi(),
    ),
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]

# ---------------------------------------------------------------------------
# ASGI application
# ---------------------------------------------------------------------------

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
