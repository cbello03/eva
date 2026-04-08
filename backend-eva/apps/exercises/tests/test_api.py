"""API-level tests for exercises — CRUD endpoints and lesson player routes.

Uses Django Ninja's TestClient for GET endpoints and direct service/view
calls for POST/PATCH/DELETE to avoid the Pydantic v2 QueryParams
model_rebuild issue with field_validator schemas in Django Ninja 1.6.
"""

from __future__ import annotations

import pytest
from ninja.testing import TestClient as NinjaTestClient

from apps.accounts.models import Role, User
from apps.accounts.schemas import LoginIn, RegisterIn
from apps.accounts.services import AuthService
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import AnswerRecord, Exercise, LessonSession
from apps.exercises.schemas import ExerciseCreateIn
from apps.exercises.services import ExerciseService
from backend_eva.urls import api

ninja_client = NinjaTestClient(api)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _create_user(email: str, role: str = Role.STUDENT, password: str = "Pass1234") -> User:
    user = AuthService.register(
        RegisterIn(email=email, password=password, display_name=email.split("@")[0])
    )
    if role != Role.STUDENT:
        user.role = role
        user.save(update_fields=["role"])
    return user


def _get_token(email: str, password: str = "Pass1234") -> str:
    pair = AuthService.login(LoginIn(email=email, password=password))
    return pair.access_token


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def teacher(db):
    return _create_user("teacher@test.com", Role.TEACHER)


@pytest.fixture
def teacher_token(teacher):
    return _get_token(teacher.email)


@pytest.fixture
def student(db):
    return _create_user("student@test.com", Role.STUDENT)


@pytest.fixture
def student_token(student):
    return _get_token(student.email)


@pytest.fixture
def course(teacher):
    return Course.objects.create(
        title="Test Course", description="Desc",
        teacher=teacher, status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def unit(course):
    return Unit.objects.create(course=course, title="Unit 1", order=1)


@pytest.fixture
def lesson(unit):
    return Lesson.objects.create(unit=unit, title="Lesson 1", order=1)


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


@pytest.fixture
def mc_exercise(teacher, lesson):
    return ExerciseService.create_exercise(
        teacher, lesson.pk,
        ExerciseCreateIn(
            exercise_type="multiple_choice",
            question_text="What is 2+2?",
            config={"options": ["3", "4", "5"], "correct_index": 1},
        ),
    )


# ------------------------------------------------------------------
# GET lesson player endpoints (via Ninja TestClient)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestStartLessonAPI:
    def test_start_returns_session(self, student_token, lesson, enrollment, mc_exercise):
        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/start",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["lesson_id"] == lesson.pk
        assert body["is_completed"] is False
        assert body["total_exercises"] == 1
        assert body["current_exercise"] is not None
        assert body["current_exercise"]["exercise_type"] == "multiple_choice"

    def test_start_unauthenticated_returns_401(self, lesson):
        resp = ninja_client.get(f"/lessons/{lesson.pk}/start")
        assert resp.status_code == 401

    def test_start_not_enrolled_returns_403(self, student_token, lesson, mc_exercise):
        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/start",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 403

    def test_start_teacher_role_returns_403(self, teacher_token, lesson, mc_exercise):
        """Teachers cannot use the student lesson player."""
        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/start",
            headers=_auth_header(teacher_token),
        )
        assert resp.status_code == 403

    def test_start_nonexistent_lesson_returns_404(self, student_token, enrollment):
        resp = ninja_client.get(
            "/lessons/99999/start",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestResumeLessonAPI:
    def test_resume_returns_current_exercise(
        self, student, student_token, lesson, enrollment, teacher, mc_exercise,
    ):
        # Create a second exercise and start the session
        ex2 = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="fill_blank",
                question_text="Capital of France?",
                config={"blank_position": 0, "accepted_answers": ["Paris"]},
            ),
        )
        ExerciseService.start_lesson(student, lesson.pk)
        ExerciseService.submit_answer(student, mc_exercise.pk, {"selected_index": 1})

        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/resume",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["current_exercise"]["id"] == ex2.pk
        assert body["progress_percentage"] > 0

    def test_resume_no_session_returns_404(self, student_token, lesson, enrollment):
        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/resume",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 404

    def test_resume_unauthenticated_returns_401(self, lesson):
        resp = ninja_client.get(f"/lessons/{lesson.pk}/resume")
        assert resp.status_code == 401


# ------------------------------------------------------------------
# Exercise CRUD — direct view function calls
# (avoids Pydantic v2 QueryParams model_rebuild issue)
# ------------------------------------------------------------------


class FakeRequest:
    """Minimal request-like object for testing view functions directly."""

    def __init__(self, user=None):
        self.auth = user
        self.META = {"REMOTE_ADDR": "127.0.0.1"}


@pytest.mark.django_db
class TestCreateExerciseAPI:
    def test_teacher_creates_exercise(self, teacher, lesson):
        from apps.exercises.api import create_exercise

        payload = ExerciseCreateIn(
            exercise_type="matching",
            question_text="Match them",
            config={"pairs": [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]},
        )
        status, out = create_exercise(FakeRequest(user=teacher), lesson.pk, payload)
        assert status == 201
        assert out.exercise_type == "matching"
        assert out.order == 1

    def test_student_cannot_create_exercise(self, student, lesson):
        from apps.exercises.api import create_exercise
        from common.exceptions import InsufficientRoleError

        payload = ExerciseCreateIn(
            exercise_type="free_text",
            question_text="Q",
            config={"rubric": "ok"},
        )
        with pytest.raises(InsufficientRoleError):
            create_exercise(FakeRequest(user=student), lesson.pk, payload)


@pytest.mark.django_db
class TestDeleteExerciseAPI:
    def test_teacher_deletes_exercise(self, teacher, lesson, mc_exercise):
        from apps.exercises.api import delete_exercise

        status, _ = delete_exercise(FakeRequest(user=teacher), mc_exercise.pk)
        assert status == 204
        assert not Exercise.objects.filter(pk=mc_exercise.pk).exists()

    def test_student_cannot_delete(self, student, lesson, mc_exercise):
        from apps.exercises.api import delete_exercise
        from common.exceptions import InsufficientRoleError

        with pytest.raises(InsufficientRoleError):
            delete_exercise(FakeRequest(user=student), mc_exercise.pk)


# ------------------------------------------------------------------
# Submit answer — direct view function call
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestSubmitAnswerAPI:
    def test_submit_correct_answer(self, student, lesson, enrollment, mc_exercise):
        from apps.exercises.api import submit_answer
        from apps.exercises.schemas import AnswerIn

        ExerciseService.start_lesson(student, lesson.pk)
        result = submit_answer(
            FakeRequest(user=student), mc_exercise.pk,
            AnswerIn(answer={"selected_index": 1}),
        )
        assert result.is_correct is True

    def test_submit_creates_answer_record(self, student, lesson, enrollment, mc_exercise):
        ExerciseService.start_lesson(student, lesson.pk)
        ExerciseService.submit_answer(student, mc_exercise.pk, {"selected_index": 1})

        records = AnswerRecord.objects.filter(student=student, exercise=mc_exercise)
        assert records.count() == 1
        record = records.first()
        assert record.is_correct is True
        assert record.is_first_attempt is True
        assert record.submitted_answer == {"selected_index": 1}

    def test_teacher_cannot_submit_answer(self, teacher, lesson, mc_exercise):
        from apps.exercises.api import submit_answer
        from apps.exercises.schemas import AnswerIn
        from common.exceptions import InsufficientRoleError

        with pytest.raises(InsufficientRoleError):
            submit_answer(
                FakeRequest(user=teacher), mc_exercise.pk,
                AnswerIn(answer={"selected_index": 0}),
            )


# ------------------------------------------------------------------
# Free text submission — storage and answer record verification
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestFreeTextSubmission:
    def test_free_text_stored_as_answer_record(self, teacher, student, lesson, enrollment):
        ex = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Explain photosynthesis",
                config={"rubric": "Clarity, accuracy, depth"},
            ),
        )
        ExerciseService.start_lesson(student, lesson.pk)
        result = ExerciseService.submit_answer(
            student, ex.pk, {"text": "Plants convert sunlight into energy."},
        )

        assert result.is_correct is False
        assert result.feedback == "Submitted for teacher review"
        assert result.correct_answer is None

        record = AnswerRecord.objects.get(student=student, exercise=ex)
        assert record.submitted_answer == {"text": "Plants convert sunlight into energy."}
        assert record.is_correct is False

    def test_free_text_not_added_to_retry_queue(self, teacher, student, lesson, enrollment):
        """Free text exercises should not be retried even though they're marked incorrect."""
        ex = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Explain gravity",
                config={"rubric": "Depth"},
            ),
        )
        session, _ = ExerciseService.start_lesson(student, lesson.pk)
        ExerciseService.submit_answer(student, ex.pk, {"text": "Gravity pulls."})

        session.refresh_from_db()
        assert ex.pk not in session.retry_queue

    def test_free_text_completes_lesson_when_only_exercise(
        self, teacher, student, lesson, enrollment,
    ):
        ex = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Describe evolution",
                config={"rubric": "Scientific accuracy"},
            ),
        )
        session, _ = ExerciseService.start_lesson(student, lesson.pk)
        ExerciseService.submit_answer(student, ex.pk, {"text": "Natural selection."})

        session.refresh_from_db()
        assert session.is_completed is True
        assert session.completed_at is not None


# ------------------------------------------------------------------
# Answer record tracking — first attempt detection
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestAnswerRecordTracking:
    def test_first_attempt_flag(self, teacher, student, lesson, enrollment):
        """First submission for an exercise is marked is_first_attempt=True."""
        ex = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q",
                config={"options": ["A", "B"], "correct_index": 0},
            ),
        )
        ExerciseService.start_lesson(student, lesson.pk)

        # First attempt — incorrect
        ExerciseService.submit_answer(student, ex.pk, {"selected_index": 1})
        # Retry — correct
        ExerciseService.submit_answer(student, ex.pk, {"selected_index": 0})

        records = list(
            AnswerRecord.objects.filter(student=student, exercise=ex)
            .order_by("answered_at")
        )
        assert len(records) == 2
        assert records[0].is_first_attempt is True
        assert records[0].is_correct is False
        assert records[1].is_first_attempt is False
        assert records[1].is_correct is True

    def test_correct_first_attempt_count(self, teacher, student, lesson, enrollment):
        """Session tracks how many exercises were answered correctly on first try."""
        ex1 = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q1",
                config={"options": ["A", "B"], "correct_index": 0},
            ),
        )
        ex2 = ExerciseService.create_exercise(
            teacher, lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q2",
                config={"options": ["X", "Y"], "correct_index": 1},
            ),
        )
        session, _ = ExerciseService.start_lesson(student, lesson.pk)

        # ex1: incorrect first, then retry correct
        ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 1})
        # ex2: correct first try
        ExerciseService.submit_answer(student, ex2.pk, {"selected_index": 1})
        # retry ex1: correct
        ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 0})

        session.refresh_from_db()
        assert session.correct_first_attempt == 1  # only ex2
        assert session.is_completed is True


# ------------------------------------------------------------------
# Progress percentage in session response
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestProgressPercentage:
    def test_progress_advances_with_answers(
        self, teacher, student, student_token, lesson, enrollment,
    ):
        for i in range(3):
            ExerciseService.create_exercise(
                teacher, lesson.pk,
                ExerciseCreateIn(
                    exercise_type="multiple_choice",
                    question_text=f"Q{i+1}",
                    config={"options": ["A", "B"], "correct_index": 0},
                ),
            )

        # Start and check initial progress
        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/start",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200
        assert resp.json()["progress_percentage"] == pytest.approx(0.0)

        # Answer first exercise
        exercises = list(lesson.exercises.order_by("order"))
        ExerciseService.submit_answer(student, exercises[0].pk, {"selected_index": 0})

        resp = ninja_client.get(
            f"/lessons/{lesson.pk}/resume",
            headers=_auth_header(student_token),
        )
        body = resp.json()
        # 1 out of 3 answered → ~33.3%
        assert body["progress_percentage"] == pytest.approx(100 / 3, abs=0.1)
