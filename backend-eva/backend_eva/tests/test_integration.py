"""Integration tests — cross-app service flows and WebSocket auth/enrollment.

Validates Requirements: 7.4, 8.1, 10.3, 19.2
"""

import uuid

import pytest
import pytest_asyncio
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings

from apps.accounts.models import Role, User
from apps.accounts.services import JWT_ALGORITHM
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import Exercise, ExerciseType, LessonSession
from apps.gamification.models import Achievement, GamificationProfile, UserAchievement, XPTransaction
from apps.notifications.models import Notification
from apps.social.consumers import ChatConsumer


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _make_jwt(user: User, *, expired: bool = False) -> str:
    """Create a valid (or expired) access JWT for the given user."""
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    exp = now - timedelta(minutes=5) if expired else now + timedelta(minutes=15)
    payload = {
        "sub": str(user.pk),
        "role": user.role,
        "type": "access",
        "exp": exp,
    }
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _make_chat_communicator(course_id: int, token: str) -> WebsocketCommunicator:
    """Build a WebsocketCommunicator for the ChatConsumer."""
    app = ChatConsumer.as_asgi()
    comm = WebsocketCommunicator(
        app, f"/ws/chat/{course_id}/?token={token}"
    )
    comm.scope["url_route"] = {"kwargs": {"course_id": course_id}}
    return comm


# ------------------------------------------------------------------
# Synchronous fixtures (for service-layer integration tests)
# ------------------------------------------------------------------


@pytest.fixture
def teacher(db):
    uid = _uid()
    return User.objects.create_user(
        username=f"integ_teacher_{uid}",
        email=f"integ_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest.fixture
def student(db):
    uid = _uid()
    return User.objects.create_user(
        username=f"integ_student_{uid}",
        email=f"integ_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def unenrolled_student(db):
    uid = _uid()
    return User.objects.create_user(
        username=f"integ_unenrolled_{uid}",
        email=f"integ_unenrolled_{uid}@test.com",
        password="Pass1234",
        display_name="Unenrolled",
        role=Role.STUDENT,
    )


@pytest.fixture
def course_with_exercises(teacher):
    """Create a published course with one unit, one lesson, and two MC exercises."""
    course = Course.objects.create(
        title="Integration Course",
        description="For integration tests",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )
    unit = Unit.objects.create(course=course, title="Unit 1", order=1)
    lesson = Lesson.objects.create(unit=unit, title="Lesson 1", order=1)
    Exercise.objects.create(
        lesson=lesson,
        exercise_type=ExerciseType.MULTIPLE_CHOICE,
        question_text="Q1: 2+2?",
        order=1,
        config={"options": ["3", "4", "5"], "correct_index": 1},
    )
    Exercise.objects.create(
        lesson=lesson,
        exercise_type=ExerciseType.MULTIPLE_CHOICE,
        question_text="Q2: 3+3?",
        order=2,
        config={"options": ["5", "6", "7"], "correct_index": 1},
    )
    return course


@pytest.fixture
def xp_achievement(db):
    """Create an achievement that triggers at 1 XP total (easy to reach in tests)."""
    return Achievement.objects.create(
        name="First Steps",
        description="Earn your first XP",
        icon="star",
        condition_type="xp_total",
        condition_value=1,
    )


@pytest.fixture
def lessons_achievement(db):
    """Create an achievement for completing 1 lesson."""
    return Achievement.objects.create(
        name="Lesson Learner",
        description="Complete your first lesson",
        icon="book",
        condition_type="lessons_completed",
        condition_value=1,
    )


# ==================================================================
# Cross-app flow: enrollment → lesson → answer → XP → achievement
# ==================================================================


@pytest.mark.django_db
class TestCrossAppFlow:
    """Full service-layer integration: enroll, play lesson, earn XP, unlock achievements."""

    def test_enrollment_creates_enrollment_record(self, student, course_with_exercises):
        """Enrolling a student creates an active enrollment."""
        from apps.courses.services import CourseService

        enrollment = CourseService.enroll(student, course_with_exercises.pk)
        assert enrollment.is_active is True
        assert enrollment.student == student
        assert enrollment.course == course_with_exercises

    def test_full_lesson_flow_awards_xp_and_checks_achievements(
        self, student, teacher, course_with_exercises, xp_achievement, lessons_achievement
    ):
        """Enrollment → start lesson → answer all correctly → XP awarded → achievements checked.

        Validates: Requirements 7.4, 8.1, 10.3
        """
        from apps.courses.services import CourseService
        from apps.exercises.services import ExerciseService
        from apps.gamification.services import GamificationService

        # 1. Enroll
        CourseService.enroll(student, course_with_exercises.pk)

        # 2. Start lesson
        lesson = course_with_exercises.units.first().lessons.first()
        session, first_exercise = ExerciseService.start_lesson(student, lesson.pk)
        assert session is not None
        assert first_exercise is not None
        assert session.is_completed is False

        # 3. Answer first exercise correctly
        result1 = ExerciseService.submit_answer(
            student, first_exercise.pk, {"selected_index": 1}
        )
        assert result1.is_correct is True

        # 4. Answer second exercise correctly
        session.refresh_from_db()
        exercises = list(lesson.exercises.order_by("order"))
        second_exercise = exercises[1]
        result2 = ExerciseService.submit_answer(
            student, second_exercise.pk, {"selected_index": 1}
        )
        assert result2.is_correct is True

        # 5. Session should be completed
        session.refresh_from_db()
        assert session.is_completed is True
        assert session.correct_first_attempt == 2

        # 6. Award XP (simulating what happens on lesson completion)
        xp_amount = session.correct_first_attempt * 10
        txn = GamificationService.award_xp(
            student=student,
            source_type="lesson",
            source_id=lesson.pk,
            amount=xp_amount,
        )
        assert txn.amount == xp_amount
        assert txn.source_type == "lesson"

        # 7. Verify XP was recorded
        assert XPTransaction.objects.filter(student=student).exists()
        profile = GamificationProfile.objects.get(student=student)
        assert profile.total_xp == xp_amount

        # 8. Verify achievements were evaluated (award_xp calls evaluate_achievements)
        user_achievements = UserAchievement.objects.filter(student=student)
        achievement_names = set(ua.achievement.name for ua in user_achievements)
        # xp_achievement requires 1 XP, lessons_achievement requires 1 completed lesson
        assert "First Steps" in achievement_names
        assert "Lesson Learner" in achievement_names

    def test_incorrect_answers_trigger_retry_then_completion(
        self, student, teacher, course_with_exercises, xp_achievement
    ):
        """Incorrect answers queue retries; completing retries finishes the lesson.

        Validates: Requirement 7.4
        """
        from apps.courses.services import CourseService
        from apps.exercises.services import ExerciseService

        CourseService.enroll(student, course_with_exercises.pk)
        lesson = course_with_exercises.units.first().lessons.first()
        session, first_ex = ExerciseService.start_lesson(student, lesson.pk)

        # Answer first exercise WRONG
        result = ExerciseService.submit_answer(
            student, first_ex.pk, {"selected_index": 0}
        )
        assert result.is_correct is False

        # Answer second exercise correctly
        session.refresh_from_db()
        exercises = list(lesson.exercises.order_by("order"))
        result2 = ExerciseService.submit_answer(
            student, exercises[1].pk, {"selected_index": 1}
        )
        assert result2.is_correct is True

        # Session not yet complete — retry queue has the first exercise
        session.refresh_from_db()
        assert session.is_completed is False
        assert first_ex.pk in session.retry_queue

        # Answer the retry correctly
        result3 = ExerciseService.submit_answer(
            student, first_ex.pk, {"selected_index": 1}
        )
        assert result3.is_correct is True

        # Now session should be complete
        session.refresh_from_db()
        assert session.is_completed is True

    def test_xp_award_creates_notification_on_achievement(
        self, student, course_with_exercises, xp_achievement
    ):
        """When an achievement is unlocked, a notification should be creatable.

        Validates: Requirements 10.3, 19.2
        """
        from apps.courses.services import CourseService
        from apps.gamification.services import GamificationService
        from apps.notifications.services import NotificationService

        CourseService.enroll(student, course_with_exercises.pk)

        # Award XP to trigger achievement
        GamificationService.award_xp(
            student=student,
            source_type="lesson",
            source_id=1,
            amount=100,
        )

        # Verify achievement was granted
        granted = UserAchievement.objects.filter(student=student)
        assert granted.count() >= 1

        # Create notification for the achievement (simulating the notification flow)
        achievement = granted.first().achievement
        notification = NotificationService.create_notification(
            recipient=student,
            notification_type="achievement_unlocked",
            title=f"Achievement Unlocked: {achievement.name}",
            body=achievement.description,
            data={"achievement_id": achievement.pk},
        )
        assert notification.recipient == student
        assert notification.notification_type == "achievement_unlocked"
        assert notification.is_read is False
        assert Notification.objects.filter(
            recipient=student, notification_type="achievement_unlocked"
        ).exists()

    def test_achievement_idempotence_across_multiple_xp_awards(
        self, student, course_with_exercises, xp_achievement
    ):
        """Multiple XP awards should not duplicate achievements.

        Validates: Requirement 10.3
        """
        from apps.courses.services import CourseService
        from apps.gamification.services import GamificationService

        CourseService.enroll(student, course_with_exercises.pk)

        # Award XP twice
        GamificationService.award_xp(student=student, source_type="lesson", source_id=1, amount=50)
        GamificationService.award_xp(student=student, source_type="lesson", source_id=2, amount=50)

        # Achievement should be granted exactly once
        count = UserAchievement.objects.filter(
            student=student, achievement=xp_achievement
        ).count()
        assert count == 1


# ==================================================================
# WebSocket authentication and enrollment enforcement
# ==================================================================


# Async fixtures for WebSocket tests

@pytest_asyncio.fixture
async def ws_teacher():
    uid = _uid()
    return await database_sync_to_async(User.objects.create_user)(
        username=f"ws_teacher_{uid}",
        email=f"ws_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="WS Teacher",
        role=Role.TEACHER,
    )


@pytest_asyncio.fixture
async def ws_student():
    uid = _uid()
    return await database_sync_to_async(User.objects.create_user)(
        username=f"ws_student_{uid}",
        email=f"ws_student_{uid}@test.com",
        password="Pass1234",
        display_name="WS Student",
        role=Role.STUDENT,
    )


@pytest_asyncio.fixture
async def ws_unenrolled():
    uid = _uid()
    return await database_sync_to_async(User.objects.create_user)(
        username=f"ws_unenrolled_{uid}",
        email=f"ws_unenrolled_{uid}@test.com",
        password="Pass1234",
        display_name="WS Unenrolled",
        role=Role.STUDENT,
    )


@pytest_asyncio.fixture
async def ws_course(ws_teacher):
    return await database_sync_to_async(Course.objects.create)(
        title="WS Test Course",
        description="For WebSocket tests",
        teacher=ws_teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest_asyncio.fixture
async def ws_enrollment(ws_student, ws_course):
    return await database_sync_to_async(Enrollment.objects.create)(
        student=ws_student, course=ws_course,
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketAuthentication:
    """Test JWT authentication on WebSocket connections."""

    async def test_valid_token_connects(self, ws_student, ws_course, ws_enrollment):
        """Enrolled student with valid JWT can connect to chat."""
        token = _make_jwt(ws_student)
        comm = _make_chat_communicator(ws_course.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        # Should receive history message
        response = await comm.receive_json_from()
        assert response["type"] == "history"
        await comm.disconnect()

    async def test_no_token_rejected(self, ws_course):
        """Connection without token is rejected."""
        app = ChatConsumer.as_asgi()
        comm = WebsocketCommunicator(app, f"/ws/chat/{ws_course.pk}/")
        comm.scope["url_route"] = {"kwargs": {"course_id": ws_course.pk}}
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_invalid_token_rejected(self, ws_course):
        """Connection with invalid JWT is rejected."""
        comm = _make_chat_communicator(ws_course.pk, "invalid.jwt.token")
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_expired_token_rejected(self, ws_student, ws_course, ws_enrollment):
        """Connection with expired JWT is rejected."""
        token = _make_jwt(ws_student, expired=True)
        comm = _make_chat_communicator(ws_course.pk, token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketEnrollmentEnforcement:
    """Test that WebSocket connections enforce course enrollment."""

    async def test_enrolled_student_connects(self, ws_student, ws_course, ws_enrollment):
        """Enrolled student can connect to course chat."""
        token = _make_jwt(ws_student)
        comm = _make_chat_communicator(ws_course.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        await comm.disconnect()

    async def test_unenrolled_student_rejected(self, ws_unenrolled, ws_course):
        """Student not enrolled in the course is rejected."""
        token = _make_jwt(ws_unenrolled)
        comm = _make_chat_communicator(ws_course.pk, token)
        connected, _ = await comm.connect()
        assert connected is False
        await comm.disconnect()

    async def test_course_teacher_connects(self, ws_teacher, ws_course):
        """Course teacher can connect to chat without enrollment."""
        token = _make_jwt(ws_teacher)
        comm = _make_chat_communicator(ws_course.pk, token)
        connected, _ = await comm.connect()
        assert connected is True
        await comm.disconnect()
