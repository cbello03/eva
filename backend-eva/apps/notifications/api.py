"""Notifications API routes — list, unread count, mark read."""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Query, Router

from apps.accounts.api import jwt_auth
from apps.notifications.schemas import NotificationOut, UnreadCountOut
from apps.notifications.services import NotificationService
from common.pagination import PaginatedResponse, PaginationParams

router = Router(tags=["notifications"], auth=jwt_auth)


@router.get("/notifications", response=PaginatedResponse)
def list_notifications(request: HttpRequest, params: PaginationParams = Query(...)):
    """Return paginated notifications for the authenticated user."""
    qs = NotificationService.get_notifications(request.auth)
    total = qs.count()
    limit = max(1, min(params.limit, 100))
    offset = max(0, params.offset)
    items = list(qs[offset : offset + limit])

    results = [
        NotificationOut(
            id=n.pk,
            notification_type=n.notification_type,
            title=n.title,
            body=n.body,
            data=n.data,
            channel=n.channel,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in items
    ]

    next_offset = offset + limit if offset + limit < total else None
    return PaginatedResponse(count=total, next_offset=next_offset, results=results)


@router.get("/notifications/unread-count", response=UnreadCountOut)
def unread_count(request: HttpRequest):
    """Return the unread notification count for the authenticated user."""
    count = NotificationService.get_unread_count(request.auth)
    return UnreadCountOut(count=count)


@router.post("/notifications/{notification_id}/read", response=NotificationOut)
def mark_read(request: HttpRequest, notification_id: int):
    """Mark a single notification as read."""
    notification = NotificationService.mark_read(request.auth, notification_id)
    return NotificationOut(
        id=notification.pk,
        notification_type=notification.notification_type,
        title=notification.title,
        body=notification.body,
        data=notification.data,
        channel=notification.channel,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.post("/notifications/read-all")
def mark_all_read(request: HttpRequest):
    """Mark all notifications as read for the authenticated user."""
    count = NotificationService.mark_all_read(request.auth)
    return {"updated": count}
