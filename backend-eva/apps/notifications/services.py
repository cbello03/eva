"""NotificationService — notification creation, delivery, and management."""

from __future__ import annotations

import logging
from typing import Any

import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import QuerySet

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationChannel
from common.exceptions import DomainError

logger = logging.getLogger(__name__)

UNREAD_COUNT_KEY_PREFIX = "notifications:unread:"


class NotificationNotFoundError(DomainError):
    status_code = 404
    code = "notification_not_found"

    def __init__(self, detail: str = "Notification not found"):
        super().__init__(detail)


def _get_redis() -> redis.Redis:
    """Return a Redis client from the configured cache URL."""
    return redis.from_url(
        settings.CACHES["default"].get("LOCATION", settings.CELERY_BROKER_URL)
    )


def _unread_key(user_id: int) -> str:
    return f"{UNREAD_COUNT_KEY_PREFIX}{user_id}"


class NotificationService:
    """Handles notification creation, delivery, and read-state management."""

    # ------------------------------------------------------------------
    # Creation & dispatch
    # ------------------------------------------------------------------

    @staticmethod
    def create_notification(
        recipient: User,
        notification_type: str,
        title: str,
        body: str,
        *,
        data: dict[str, Any] | None = None,
        channel: str = NotificationChannel.IN_APP,
    ) -> Notification:
        """Create a notification and dispatch to the configured channels."""
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {},
            channel=channel,
        )

        # Increment Redis unread count
        try:
            r = _get_redis()
            r.incr(_unread_key(recipient.pk))
        except Exception:
            logger.warning("Failed to increment Redis unread count for user %s", recipient.pk)

        # Dispatch based on channel
        if channel in (NotificationChannel.IN_APP, NotificationChannel.BOTH):
            NotificationService._send_in_app(notification)

        if channel in (NotificationChannel.EMAIL, NotificationChannel.BOTH):
            from apps.notifications.tasks import send_email_notification

            send_email_notification.delay(notification.pk)

        return notification

    # ------------------------------------------------------------------
    # In-app delivery via WebSocket
    # ------------------------------------------------------------------

    @staticmethod
    def _send_in_app(notification: Notification) -> None:
        """Push notification to the user's WebSocket channel group."""
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer not available; skipping in-app delivery")
            return

        group_name = f"notifications_{notification.recipient_id}"
        payload = {
            "type": "send_notification",
            "notification": {
                "id": notification.pk,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "body": notification.body,
                "data": notification.data,
                "channel": notification.channel,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
            },
        }
        try:
            async_to_sync(channel_layer.group_send)(group_name, payload)
        except Exception:
            logger.warning(
                "Failed to send in-app notification %s to user %s",
                notification.pk,
                notification.recipient_id,
            )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_notifications(user: User) -> QuerySet[Notification]:
        """Return all notifications for *user*, newest first."""
        return Notification.objects.filter(recipient=user).order_by("-created_at")

    @staticmethod
    def get_unread_count(user: User) -> int:
        """Return unread count, preferring Redis cache with DB fallback."""
        try:
            r = _get_redis()
            cached = r.get(_unread_key(user.pk))
            if cached is not None:
                return int(cached)
        except Exception:
            logger.warning("Redis unavailable for unread count; falling back to DB")

        count = Notification.objects.filter(recipient=user, is_read=False).count()

        # Warm the cache
        try:
            r = _get_redis()
            r.set(_unread_key(user.pk), count)
        except Exception:
            pass

        return count

    # ------------------------------------------------------------------
    # Read-state management
    # ------------------------------------------------------------------

    @staticmethod
    def mark_read(user: User, notification_id: int) -> Notification:
        """Mark a single notification as read."""
        try:
            notification = Notification.objects.get(pk=notification_id, recipient=user)
        except Notification.DoesNotExist:
            raise NotificationNotFoundError()

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read", "updated_at"])

            try:
                r = _get_redis()
                r.decr(_unread_key(user.pk))
                # Prevent negative counts
                if int(r.get(_unread_key(user.pk)) or 0) < 0:
                    r.set(_unread_key(user.pk), 0)
            except Exception:
                logger.warning("Failed to decrement Redis unread count for user %s", user.pk)

        return notification

    @staticmethod
    def mark_all_read(user: User) -> int:
        """Mark all unread notifications as read. Returns count updated."""
        count = Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

        try:
            r = _get_redis()
            r.set(_unread_key(user.pk), 0)
        except Exception:
            logger.warning("Failed to reset Redis unread count for user %s", user.pk)

        return count
