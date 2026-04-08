"""Collaboration WebSocket consumer for shared workspaces."""

from __future__ import annotations

import json
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.accounts.services import JWT_ALGORITHM
from apps.collaboration.models import CollabGroup, CollabGroupMember


class CollabConsumer(AsyncJsonWebsocketConsumer):
    """Django Channels consumer for collaborative exercise workspaces.

    Connection URL: ``ws://<host>/ws/collab/<exercise_id>/<group_id>/?token=<jwt>``
    """

    async def connect(self) -> None:
        self.exercise_id = self.scope["url_route"]["kwargs"]["exercise_id"]
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.room_group = f"collab_{self.exercise_id}_{self.group_id}"

        # Authenticate via JWT query param
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user

        # Verify group membership
        is_member = await self._check_membership()
        if not is_member:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Send current workspace state
        state = await self._get_workspace_state()
        await self.send_json({"type": "workspace_state", "state": state})

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive_json(self, content: dict, **kwargs) -> None:
        """Handle workspace update from a group member."""
        state_update = content.get("state")
        if state_update is None:
            await self.send_json({"type": "error", "detail": "Missing state"})
            return

        await self._update_workspace(state_update)

        # Broadcast to all group members
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "workspace.update",
                "state": state_update,
                "author_id": self.user.pk,
                "author_display_name": self.user.display_name,
            },
        )

    async def workspace_update(self, event: dict) -> None:
        """Deliver workspace update to the WebSocket client."""
        await self.send_json({
            "type": "workspace_update",
            "state": event["state"],
            "author_id": event["author_id"],
            "author_display_name": event["author_display_name"],
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _authenticate(self) -> User | None:
        """Authenticate user from JWT token in query string."""
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]
        if not token:
            return None

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

    @database_sync_to_async
    def _check_membership(self) -> bool:
        """Check if user is a member of this collaboration group."""
        return CollabGroupMember.objects.filter(
            group_id=self.group_id,
            student=self.user,
        ).exists()

    @database_sync_to_async
    def _get_workspace_state(self) -> dict:
        """Return the current workspace state for the group."""
        try:
            group = CollabGroup.objects.get(pk=self.group_id)
            return group.workspace_state
        except CollabGroup.DoesNotExist:
            return {}

    @database_sync_to_async
    def _update_workspace(self, state: dict) -> None:
        """Update workspace state and last_contribution_at for the member."""
        CollabGroup.objects.filter(pk=self.group_id).update(
            workspace_state=state,
            updated_at=tz.now(),
        )
        CollabGroupMember.objects.filter(
            group_id=self.group_id,
            student=self.user,
        ).update(last_contribution_at=tz.now())
