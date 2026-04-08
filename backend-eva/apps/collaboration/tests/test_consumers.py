"""Tests for CollabConsumer — WebSocket workspace updates, auth, membership enforcement."""

import uuid

import pytest
import pytest_asyncio
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings

from apps.accounts.models import Role, User
from apps.accounts.services import JWT_ALGORITHM
from apps.collaboration.consumers import CollabConsumer
from apps.collaboration.models import CollabGroup, CollabGroupMember
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import Exercise, ExerciseType


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


def _make_communicator(
    exercise_id: int, group_id: int, token: str
) -> WebsocketCommunicator:
    """Build a WebsocketCommunicator for the CollabConsumer."""
    app = CollabConsumer.as_asgi()
    communicator = WebsocketCommunicator(
        app,
        f"/ws/collab/{exercise_id}/{group_id}/?token={token}",
    )
    communicator.scope["url_route"] = {
        "kwargs": {"exercise_id": exercise_id, "group_id": group_id}
    }
    return communicator


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest_asyncio.fixture
async def teacher():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"collab_teacher_{uid}",
        email=f"collab_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest_asyncio.fixture
async def student():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"collab_student_{uid}",
        email=f"collab_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest_asyncio.fixture
async def student2():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"collab_student2_{uid}",
        email=f"collab_student2_{uid}@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
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
async def lesson(course):
    @database_sync_to_async
    def _create():
        unit = Unit.objects.create(course=course, title="Unit 1", order=1)
        return Lesson.objects.create(unit=unit, title="Lesson 1", order=1)

    return await _create()


@pytest_asyncio.fixture
async def collab_exercise(lesson):
    return await database_sync_to_async(Exercise.objects.create)(
        lesson=lesson,
        exercise_type=ExerciseType.FREE_TEXT,
        question_text="Collaborative task",
        order=1,
        config={"model_answer": "answer", "rubric": "rubric"},
        is_collaborative=True,
        collab_group_size=3,
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


@pytest_asyncio.fixture
async def group(collab_exercise):
    return await database_sync_to_async(CollabGroup.objects.create)(
        exercise=collab_exercise, max_size=3, workspace_state={"code": "initial"}
    )


@pytest_asyncio.fixture
async def membership(group, student):
    return await database_sync_to_async(CollabGroupMember.objects.create)(
        group=group, student=student
    )


@pytest_asyncio.fixture
async def membership2(group, student2):
    return await database_sync_to_async(CollabGroupMember.objects.create)(
        group=group, student=student2
    )


# ------------------------------------------------------------------
# Connection tests
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestCollabConsumerConnect:
    async def test_member_connects_and_receives_state(
        self, student, collab_exercise, group, membership
    ):
        token = _make_jwt(student)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        response = await comm.receive_json_from()
        assert response["type"] == "workspace_state"
        assert response["state"] == {"code": "initial"}
        await comm.disconnect()

    async def test_no_token_rejected(self, collab_exercise, group):
        app = CollabConsumer.as_asgi()
        comm = WebsocketCommunicator(
            app, f"/ws/collab/{collab_exercise.pk}/{group.pk}/"
        )
        comm.scope["url_route"] = {
            "kwargs": {
                "exercise_id": collab_exercise.pk,
                "group_id": group.pk,
            }
        }
        connected, code = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_invalid_token_rejected(self, collab_exercise, group):
        comm = _make_communicator(collab_exercise.pk, group.pk, "bad.jwt.token")
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_non_member_rejected(
        self, student2, collab_exercise, group
    ):
        """Student who is not a group member should be rejected."""
        token = _make_jwt(student2)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()


# ------------------------------------------------------------------
# Workspace update flow
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestCollabConsumerWorkspaceUpdates:
    async def test_send_state_update(
        self, student, collab_exercise, group, membership
    ):
        token = _make_jwt(student)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # workspace_state

        await comm.send_json_to({"state": {"code": "updated"}})
        response = await comm.receive_json_from()
        assert response["type"] == "workspace_update"
        assert response["state"] == {"code": "updated"}
        assert response["author_id"] == student.pk
        await comm.disconnect()

    async def test_missing_state_returns_error(
        self, student, collab_exercise, group, membership
    ):
        token = _make_jwt(student)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # workspace_state

        await comm.send_json_to({"no_state_key": True})
        response = await comm.receive_json_from()
        assert response["type"] == "error"
        assert "Missing state" in response["detail"]
        await comm.disconnect()

    async def test_workspace_state_persisted(
        self, student, collab_exercise, group, membership
    ):
        token = _make_jwt(student)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # workspace_state

        await comm.send_json_to({"state": {"code": "persisted"}})
        await comm.receive_json_from()  # workspace_update

        @database_sync_to_async
        def check_db():
            g = CollabGroup.objects.get(pk=group.pk)
            return g.workspace_state

        state = await check_db()
        assert state == {"code": "persisted"}
        await comm.disconnect()

    async def test_contribution_timestamp_updated(
        self, student, collab_exercise, group, membership
    ):
        token = _make_jwt(student)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # workspace_state

        await comm.send_json_to({"state": {"code": "work"}})
        await comm.receive_json_from()  # workspace_update

        @database_sync_to_async
        def check_contribution():
            m = CollabGroupMember.objects.get(group=group, student=student)
            return m.last_contribution_at

        ts = await check_contribution()
        assert ts is not None
        await comm.disconnect()


# ------------------------------------------------------------------
# Disconnect
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestCollabConsumerDisconnect:
    async def test_clean_disconnect(
        self, student, collab_exercise, group, membership
    ):
        token = _make_jwt(student)
        comm = _make_communicator(collab_exercise.pk, group.pk, token)
        await comm.connect()
        await comm.receive_json_from()  # workspace_state
        await comm.disconnect()
        # No exception means clean disconnect
