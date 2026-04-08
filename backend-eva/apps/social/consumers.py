"""Chat WebSocket consumer for real-time course chat rooms."""

from __future__ import annotations

import json
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from apps.accounts.models import User
from apps.accounts.services import JWT_ALGORITHM
from apps.courses.models import Course, Enrollment
from apps.social.models import ChatMessage


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Django Channels consumer for per-course real-time chat.

    Connection URL: ``ws://<host>/ws/chat/<course_id>/?token=<jwt>``
    """

    async def connect(self) -> None:
        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        self.room_group = f"chat_{self.course_id}"

        # Authenticate via JWT query param
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user

        # Verify enrollment
        enrolled = await self._check_enrollment()
        if not enrolled:
            await self.close(code=4003)
            return

        # Join channel group
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Send last 50 messages as history
        history = await self._get_history()
        await self.send_json({"type": "history", "messages": history})

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive_json(self, content: dict, **kwargs) -> None:
        """Handle incoming chat message."""
        message_content = content.get("content", "").strip()
        if not message_content or len(message_content) > 2000:
            await self.send_json({"type": "error", "detail": "Invalid message"})
            return

        msg = await self._persist_message(message_content)

        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat.message",
                "message": msg,
            },
        )

    async def chat_message(self, event: dict) -> None:
        """Deliver a chat message to the WebSocket client."""
        await self.send_json({"type": "message", "message": event["message"]})

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
    def _check_enrollment(self) -> bool:
        """Check if user is enrolled, is the course teacher, or is admin."""
        from apps.accounts.models import Role

        if self.user.role == Role.ADMIN:
            return True
        try:
            course = Course.objects.get(pk=self.course_id)
        except Course.DoesNotExist:
            return False
        if self.user.role == Role.TEACHER and course.teacher_id == self.user.pk:
            return True
        return Enrollment.objects.filter(
            student=self.user, course_id=self.course_id, is_active=True
        ).exists()

    @database_sync_to_async
    def _get_history(self) -> list[dict]:
        """Return last 50 messages for this course chat room."""
        messages = (
            ChatMessage.objects.filter(course_id=self.course_id)
            .select_related("author")
            .order_by("-sent_at")[:50]
        )
        # Reverse to chronological order
        return [
            {
                "id": m.pk,
                "course_id": m.course_id,
                "author_id": m.author_id,
                "author_display_name": m.author.display_name,
                "content": m.content,
                "sent_at": m.sent_at.isoformat(),
            }
            for m in reversed(messages)
        ]

    @database_sync_to_async
    def _persist_message(self, content: str) -> dict:
        """Save a chat message to the database and return serialized data."""
        from common.sanitization import sanitize_html

        msg = ChatMessage.objects.create(
            course_id=self.course_id,
            author=self.user,
            content=sanitize_html(content),
        )
        return {
            "id": msg.pk,
            "course_id": msg.course_id,
            "author_id": msg.author_id,
            "author_display_name": self.user.display_name,
            "content": msg.content,
            "sent_at": msg.sent_at.isoformat(),
        }
