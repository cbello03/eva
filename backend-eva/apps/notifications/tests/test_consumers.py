"""Tests for NotificationConsumer — WebSocket connect, disconnect, notification delivery."""

import uuid

import pytest
import pytest_asyncio
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings

from apps.accounts.models import Role, User
from apps.accounts.services import JWT_ALGORITHM
from apps.notifications.consumers import NotificationConsumer


def _make_jwt(user: User) -> str:
    """Create a valid access JWT for the given user."""
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone

    payload = {
        "sub": str(user.pk),
        "role": user.role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _make_communicator(token: str) -> WebsocketCommunicator:
    """Build a WebsocketCommunicator for the NotificationConsumer."""
    app = NotificationConsumer.as_asgi()
    return WebsocketCommunicator(app, f"/ws/notifications/?token={token}")


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest_asyncio.fixture
async def student():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"notif_student_{uid}",
        email=f"notif_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest_asyncio.fixture
async def student2():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"notif_student2_{uid}",
        email=f"notif_student2_{uid}@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
    )


# ------------------------------------------------------------------
# Connection tests
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestNotificationConsumerConnect:
    async def test_valid_token_connects(self, student):
        token = _make_jwt(student)
        comm = _make_communicator(token)
        connected, _ = await comm.connect()
        assert connected is True
        await comm.disconnect()

    async def test_no_token_rejected(self):
        app = NotificationConsumer.as_asgi()
        comm = WebsocketCommunicator(app, "/ws/notifications/")
        connected, code = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_invalid_token_rejected(self):
        comm = _make_communicator("invalid.jwt.token")
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_expired_token_rejected(self, student):
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": str(student.pk),
            "role": student.role,
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = pyjwt.encode(
            payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        comm = _make_communicator(expired_token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_refresh_token_type_rejected(self, student):
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": str(student.pk),
            "role": student.role,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
        comm = _make_communicator(token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_nonexistent_user_rejected(self):
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": "99999",
            "role": "student",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
        comm = _make_communicator(token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()


# ------------------------------------------------------------------
# Notification delivery via channel layer
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestNotificationDelivery:
    async def test_receives_notification_event(self, student):
        from channels.layers import get_channel_layer

        token = _make_jwt(student)
        comm = _make_communicator(token)
        connected, _ = await comm.connect()
        assert connected is True

        # Send a notification event through the channel layer
        channel_layer = get_channel_layer()
        group_name = f"notifications_{student.pk}"
        await channel_layer.group_send(
            group_name,
            {
                "type": "send_notification",
                "notification": {
                    "id": 1,
                    "notification_type": "achievement_unlock",
                    "title": "Achievement!",
                    "body": "You earned a badge",
                    "data": {},
                    "channel": "in_app",
                    "is_read": False,
                    "created_at": "2025-01-01T00:00:00Z",
                },
            },
        )

        response = await comm.receive_json_from()
        assert response["type"] == "notification"
        assert response["notification"]["id"] == 1
        assert response["notification"]["title"] == "Achievement!"
        assert response["notification"]["notification_type"] == "achievement_unlock"
        await comm.disconnect()

    async def test_notification_not_delivered_to_other_user(self, student, student2):
        from channels.layers import get_channel_layer

        token1 = _make_jwt(student)
        token2 = _make_jwt(student2)
        comm1 = _make_communicator(token1)
        comm2 = _make_communicator(token2)

        await comm1.connect()
        await comm2.connect()

        # Send notification only to student's group
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"notifications_{student.pk}",
            {
                "type": "send_notification",
                "notification": {
                    "id": 1,
                    "notification_type": "test",
                    "title": "For student only",
                    "body": "Body",
                    "data": {},
                    "channel": "in_app",
                    "is_read": False,
                    "created_at": "2025-01-01T00:00:00Z",
                },
            },
        )

        # student should receive it
        response = await comm1.receive_json_from()
        assert response["notification"]["title"] == "For student only"

        # student2 should NOT receive anything (timeout)
        assert await comm2.receive_nothing() is True

        await comm1.disconnect()
        await comm2.disconnect()


# ------------------------------------------------------------------
# Disconnect
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestNotificationConsumerDisconnect:
    async def test_clean_disconnect(self, student):
        token = _make_jwt(student)
        comm = _make_communicator(token)
        await comm.connect()
        await comm.disconnect()
        # No exception means clean disconnect
