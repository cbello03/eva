"""Notification WebSocket consumer for real-time in-app delivery."""

from __future__ import annotations

from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from apps.accounts.models import User
from apps.accounts.services import JWT_ALGORITHM


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Django Channels consumer for per-user notification delivery.

    Connection URL: ``ws://<host>/ws/notifications/?token=<jwt>``
    """

    async def connect(self) -> None:
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f"notifications_{user.pk}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def send_notification(self, event: dict) -> None:
        """Handler for ``send_notification`` events from the channel layer."""
        await self.send_json(
            {"type": "notification", "notification": event["notification"]}
        )

    # ------------------------------------------------------------------
    # Authentication helper (same pattern as ChatConsumer)
    # ------------------------------------------------------------------

    async def _authenticate(self) -> User | None:
        """Validate JWT from query string and return the User or None."""
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])
        if not token_list:
            return None

        token = token_list[0]
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["sub", "role", "exp", "type"]},
            )
        except jwt.PyJWTError:
            return None

        if payload.get("type") != "access":
            return None

        return await self._get_user(int(payload["sub"]))

    @database_sync_to_async
    def _get_user(self, user_id: int) -> User | None:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
