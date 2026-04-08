"""Tests for ChatConsumer — WebSocket connect, disconnect, message flow, enrollment enforcement."""

import uuid

import pytest
import pytest_asyncio
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings

from apps.accounts.models import Role, User
from apps.accounts.services import JWT_ALGORITHM
from apps.courses.models import Course, Enrollment
from apps.social.consumers import ChatConsumer
from apps.social.models import ChatMessage


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


def _make_communicator(course_id: int, token: str) -> WebsocketCommunicator:
    """Build a WebsocketCommunicator for the ChatConsumer."""
    app = ChatConsumer.as_asgi()
    communicator = WebsocketCommunicator(
        app,
        f"/ws/chat/{course_id}/?token={token}",
    )
    communicator.scope["url_route"] = {"kwargs": {"course_id": course_id}}
    return communicator


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest_asyncio.fixture
async def teacher():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"chat_teacher_{uid}",
        email=f"chat_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest_asyncio.fixture
async def student():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"chat_student_{uid}",
        email=f"chat_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest_asyncio.fixture
async def student2():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"chat_student2_{uid}",
        email=f"chat_student2_{uid}@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
    )


@pytest_asyncio.fixture
async def admin_user():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"chat_admin_{uid}",
        email=f"chat_admin_{uid}@test.com",
        password="Pass1234",
        display_name="Admin",
        role=Role.ADMIN,
    )


@pytest_asyncio.fixture
async def course(teacher):
    return await database_sync_to_async(Course.objects.create)(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest_asyncio.fixture
async def enrollment(student, course):
    return await database_sync_to_async(Enrollment.objects.create)(
        student=student, course=course
    )


@pytest_asyncio.fixture
async def enrollment2(student2, course):
    return await database_sync_to_async(Enrollment.objects.create)(
        student=student2, course=course
    )


# ------------------------------------------------------------------
# Connection tests
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerConnect:
    async def test_enrolled_student_connects(self, student, course, enrollment):
        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        # Should receive history message on connect
        response = await comm.receive_json_from()
        assert response["type"] == "history"
        assert isinstance(response["messages"], list)
        await comm.disconnect()

    async def test_teacher_owner_connects(self, teacher, course):
        token = _make_jwt(teacher)
        comm = _make_communicator(course.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        await comm.receive_json_from()  # history
        await comm.disconnect()

    async def test_admin_connects(self, admin_user, course):
        token = _make_jwt(admin_user)
        comm = _make_communicator(course.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        await comm.receive_json_from()  # history
        await comm.disconnect()

    async def test_no_token_rejected(self, course):
        app = ChatConsumer.as_asgi()
        comm = WebsocketCommunicator(app, f"/ws/chat/{course.pk}/")
        comm.scope["url_route"] = {"kwargs": {"course_id": course.pk}}
        connected, code = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_invalid_token_rejected(self, course):
        comm = _make_communicator(course.pk, "invalid.jwt.token")
        connected, code = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_expired_token_rejected(self, student, course, enrollment):
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
        comm = _make_communicator(course.pk, expired_token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()


# ------------------------------------------------------------------
# Enrollment enforcement
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatEnrollmentEnforcement:
    async def test_unenrolled_student_rejected(self, student, course):
        """Student not enrolled should be rejected (code 4003)."""
        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        connected, code = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_nonexistent_course_rejected(self, student):
        token = _make_jwt(student)
        comm = _make_communicator(99999, token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()


# ------------------------------------------------------------------
# Message flow
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerMessageFlow:
    async def test_send_message_persisted(self, student, course, enrollment):
        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # history

        await comm.send_json_to({"content": "Hello world"})
        response = await comm.receive_json_from()
        assert response["type"] == "message"
        assert response["message"]["content"] == "Hello world"
        assert response["message"]["author_id"] == student.pk

        # Verify persisted to DB
        count = await database_sync_to_async(
            ChatMessage.objects.filter(course=course, author=student).count
        )()
        assert count == 1
        await comm.disconnect()

    async def test_empty_message_rejected(self, student, course, enrollment):
        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # history

        await comm.send_json_to({"content": ""})
        response = await comm.receive_json_from()
        assert response["type"] == "error"
        await comm.disconnect()

    async def test_too_long_message_rejected(self, student, course, enrollment):
        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # history

        await comm.send_json_to({"content": "x" * 2001})
        response = await comm.receive_json_from()
        assert response["type"] == "error"
        await comm.disconnect()

    async def test_history_on_connect(self, student, course, enrollment):
        # Pre-populate some messages
        @database_sync_to_async
        def create_messages():
            for i in range(3):
                ChatMessage.objects.create(
                    course=course, author=student, content=f"Msg {i}"
                )

        await create_messages()

        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        await comm.connect()
        response = await comm.receive_json_from()
        assert response["type"] == "history"
        assert len(response["messages"]) == 3
        await comm.disconnect()

    async def test_history_limited_to_50(self, student, course, enrollment):
        @database_sync_to_async
        def create_many_messages():
            for i in range(60):
                ChatMessage.objects.create(
                    course=course, author=student, content=f"Msg {i}"
                )

        await create_many_messages()

        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        await comm.connect()
        response = await comm.receive_json_from()
        assert response["type"] == "history"
        assert len(response["messages"]) == 50
        await comm.disconnect()


# ------------------------------------------------------------------
# Disconnect
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestChatConsumerDisconnect:
    async def test_clean_disconnect(self, student, course, enrollment):
        token = _make_jwt(student)
        comm = _make_communicator(course.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # history
        await comm.disconnect()
        # No exception means clean disconnect
