"""Notifications app Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ninja import Schema


class NotificationOut(Schema):
    """Notification representation in API responses."""

    id: int
    notification_type: str
    title: str
    body: str
    data: dict[str, Any]
    channel: str
    is_read: bool
    created_at: datetime


class UnreadCountOut(Schema):
    """Unread notification count response."""

    count: int
