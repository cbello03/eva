"""Tests for ExerciseService — exercise CRUD and lesson player logic."""

import pytest

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import AnswerRecord, Exercise, LessonSession
from apps.exercises.schemas import ExerciseCreateIn, ExerciseUpdateIn
from apps.exercises.services import (
    ExerciseAlreadyAnsweredError,
    ExerciseNotFoundError,
    ExerciseService,
    LessonAlreadyCompletedError,
    LessonNotFoundError,
    LessonSessionNotFoundError,
)
from common.exceptions import InsufficientRoleError, NotEnrolledError


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def teacher(db):
    return User.objects.create_user(
        username="teacher",
        email="teacher@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest.fixture
def other_teacher(db):
    return User.objects.create_user(
        username="other",
        email="other@test.com",
        password="Pass1234",
        display_name="Other",
        role=Role.TEACHER,
    )


@pytest.fixture
def student(db):
    return User.objects.create_user(
        username="student",
        email="student@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def course(db, teacher):
    return Course.objects.create(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
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
def mc_data():
    return ExerciseCreateIn(
        exercise_type="multiple_choice",
        question_text="What is 2+2?",
        config={"options": ["3", "4", "5"], "correct_index": 1},
    )


@pytest.fixture
def fill_data():
    return ExerciseCreateIn(
        exercise_type="fill_blank",
        question_text="The capital of France is ___",
        config={"blank_position": 0, "accepted_answers": ["Paris", "paris"]},
    )


@pytest.fixture
def matching_data():
    return ExerciseCreateIn(
        exercise_type="matching",
        question_text="Match countries to capitals",
        config={
            "pairs": [
                {"left": "France", "right": "Paris"},
                {"left": "Spain", "right": "Madrid"},
            ]
        },
    )


@pytest.fixture
def free_text_data():
    return ExerciseCreateIn(
        exercise_type="free_text",
        question_text="Explain gravity",
        config={"rubric": "Clarity and depth"},
    )


# ------------------------------------------------------------------
# Exercise CRUD tests
# ------------------------------------------------------------------


class TestCreateExercise:
    def test_creates_exercise(self, teacher, lesson, mc_data):
        ex = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        assert ex.pk is not None
        assert ex.order == 1
        assert ex.exercise_type == "multiple_choice"

    def test_auto_increments_order(self, teacher, lesson, mc_data, fill_data):
        ex1 = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        ex2 = ExerciseService.create_exercise(teacher, lesson.pk, fill_data)
        assert ex1.order == 1
        assert ex2.order == 2

    def test_sanitizes_question_text(self, teacher, lesson):
        data = ExerciseCreateIn(
            exercise_type="free_text",
            question_text='<script>alert("xss")</script><b>Bold</b>',
            config={"rubric": "ok"},
        )
        ex = ExerciseService.create_exercise(teacher, lesson.pk, data)
        assert "<script>" not in ex.question_text
        assert "<b>Bold</b>" in ex.question_text

    def test_lesson_not_found(self, teacher, mc_data):
        with pytest.raises(LessonNotFoundError):
            ExerciseService.create_exercise(teacher, 9999, mc_data)

    def test_non_owner_rejected(self, other_teacher, lesson, mc_data):
        with pytest.raises(InsufficientRoleError):
            ExerciseService.create_exercise(other_teacher, lesson.pk, mc_data)


class TestUpdateExercise:
    def test_updates_fields(self, teacher, lesson, mc_data):
        ex = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        updated = ExerciseService.update_exercise(
            teacher, ex.pk, ExerciseUpdateIn(difficulty=3, topic="math")
        )
        assert updated.difficulty == 3
        assert updated.topic == "math"

    def test_validates_config_on_update(self, teacher, lesson, mc_data):
        ex = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        # Invalid config: only 1 option for multiple_choice
        with pytest.raises(Exception):
            ExerciseService.update_exercise(
                teacher,
                ex.pk,
                ExerciseUpdateIn(config={"options": ["only"], "correct_index": 0}),
            )

    def test_exercise_not_found(self, teacher):
        with pytest.raises(ExerciseNotFoundError):
            ExerciseService.update_exercise(
                teacher, 9999, ExerciseUpdateIn(topic="x")
            )

    def test_non_owner_rejected(self, other_teacher, teacher, lesson, mc_data):
        ex = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        with pytest.raises(InsufficientRoleError):
            ExerciseService.update_exercise(
                other_teacher, ex.pk, ExerciseUpdateIn(topic="x")
            )


class TestDeleteExercise:
    def test_deletes_and_renumbers(self, teacher, lesson, mc_data, fill_data, matching_data):
        ex1 = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        ex2 = ExerciseService.create_exercise(teacher, lesson.pk, fill_data)
        ex3 = ExerciseService.create_exercise(teacher, lesson.pk, matching_data)

        ExerciseService.delete_exercise(teacher, ex2.pk)

        remaining = list(lesson.exercises.order_by("order").values_list("pk", "order"))
        assert remaining == [(ex1.pk, 1), (ex3.pk, 2)]

    def test_exercise_not_found(self, teacher):
        with pytest.raises(ExerciseNotFoundError):
            ExerciseService.delete_exercise(teacher, 9999)

    def test_non_owner_rejected(self, other_teacher, teacher, lesson, mc_data):
        ex = ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        with pytest.raises(InsufficientRoleError):
            ExerciseService.delete_exercise(other_teacher, ex.pk)


# ------------------------------------------------------------------
# Lesson player tests
# ------------------------------------------------------------------


class TestStartLesson:
    def test_starts_new_session(self, student, lesson, enrollment, teacher, mc_data):
        ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        session, exercise = ExerciseService.start_lesson(student, lesson.pk)
        assert session.pk is not None
        assert session.total_exercises == 1
        assert session.current_exercise_index == 0
        assert exercise is not None

    def test_returns_none_exercise_when_empty(self, student, lesson, enrollment):
        session, exercise = ExerciseService.start_lesson(student, lesson.pk)
        assert session.total_exercises == 0
        assert exercise is None

    def test_resumes_existing_session(self, student, lesson, enrollment, teacher, mc_data):
        ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        s1, _ = ExerciseService.start_lesson(student, lesson.pk)
        s2, _ = ExerciseService.start_lesson(student, lesson.pk)
        assert s1.pk == s2.pk

    def test_raises_if_already_completed(self, student, lesson, enrollment, teacher, mc_data):
        ExerciseService.create_exercise(teacher, lesson.pk, mc_data)
        session, _ = ExerciseService.start_lesson(student, lesson.pk)
        session.is_completed = True
        session.save()
        with pytest.raises(LessonAlreadyCompletedError):
            ExerciseService.start_lesson(student, lesson.pk)

    def test_not_enrolled_rejected(self, student, lesson):
        with pytest.raises(NotEnrolledError):
            ExerciseService.start_lesson(student, lesson.pk)

    def test_lesson_not_found(self, student):
        with pytest.raises(LessonNotFoundError):
            ExerciseService.start_lesson(student, 9999)


class TestSubmitAnswer:
    def _setup_lesson(self, teacher, lesson, student, enrollment):
        """Create 2 MC exercises and start a session."""
        ex1 = ExerciseService.create_exercise(
            teacher,
            lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q1",
                config={"options": ["A", "B"], "correct_index": 0},
            ),
        )
        ex2 = ExerciseService.create_exercise(
            teacher,
            lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q2",
                config={"options": ["X", "Y"], "correct_index": 1},
            ),
        )
        session, _ = ExerciseService.start_lesson(student, lesson.pk)
        return session, ex1, ex2

    def test_correct_answer(self, teacher, lesson, student, enrollment):
        session, ex1, ex2 = self._setup_lesson(teacher, lesson, student, enrollment)
        result = ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 0})
        assert result.is_correct is True
        assert result.correct_answer is None

    def test_incorrect_answer_returns_correct(self, teacher, lesson, student, enrollment):
        session, ex1, ex2 = self._setup_lesson(teacher, lesson, student, enrollment)
        result = ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 1})
        assert result.is_correct is False
        assert result.correct_answer == {"selected_index": 0}

    def test_incorrect_adds_to_retry_queue(self, teacher, lesson, student, enrollment):
        session, ex1, ex2 = self._setup_lesson(teacher, lesson, student, enrollment)
        ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 1})
        session.refresh_from_db()
        assert ex1.pk in session.retry_queue

    def test_correct_first_attempt_incremented(self, teacher, lesson, student, enrollment):
        session, ex1, ex2 = self._setup_lesson(teacher, lesson, student, enrollment)
        ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 0})
        session.refresh_from_db()
        assert session.correct_first_attempt == 1

    def test_wrong_exercise_raises(self, teacher, lesson, student, enrollment):
        session, ex1, ex2 = self._setup_lesson(teacher, lesson, student, enrollment)
        # ex2 is not the current exercise (ex1 is)
        with pytest.raises(ExerciseAlreadyAnsweredError):
            ExerciseService.submit_answer(student, ex2.pk, {"selected_index": 1})

    def test_no_session_raises(self, teacher, lesson, student, enrollment):
        ex = ExerciseService.create_exercise(
            teacher,
            lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q",
                config={"options": ["A", "B"], "correct_index": 0},
            ),
        )
        with pytest.raises(LessonSessionNotFoundError):
            ExerciseService.submit_answer(student, ex.pk, {"selected_index": 0})

    def test_lesson_completion(self, teacher, lesson, student, enrollment):
        session, ex1, ex2 = self._setup_lesson(teacher, lesson, student, enrollment)
        # Answer both correctly
        ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 0})
        ExerciseService.submit_answer(student, ex2.pk, {"selected_index": 1})
        session.refresh_from_db()
        assert session.is_completed is True
        assert session.completed_at is not None
        assert session.correct_first_attempt == 2

    def test_retry_flow(self, teacher, lesson, student, enrollment):
        """Wrong answer → retry at end → correct on retry → completed."""
        # Single exercise lesson
        ex = ExerciseService.create_exercise(
            teacher,
            lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q1",
                config={"options": ["A", "B"], "correct_index": 0},
            ),
        )
        session, _ = ExerciseService.start_lesson(student, lesson.pk)

        # Answer incorrectly
        result = ExerciseService.submit_answer(student, ex.pk, {"selected_index": 1})
        assert result.is_correct is False
        session.refresh_from_db()
        assert session.retry_queue == [ex.pk]
        assert session.is_completed is False

        # Retry: the exercise appears again
        result2 = ExerciseService.submit_answer(student, ex.pk, {"selected_index": 0})
        assert result2.is_correct is True
        session.refresh_from_db()
        assert session.is_completed is True


class TestSubmitAnswerTypes:
    """Test answer evaluation for each exercise type."""

    def _make_exercise_and_session(self, teacher, lesson, student, enrollment, data):
        ex = ExerciseService.create_exercise(teacher, lesson.pk, data)
        session, _ = ExerciseService.start_lesson(student, lesson.pk)
        return ex

    def test_fill_blank_correct(self, teacher, lesson, student, enrollment):
        ex = self._make_exercise_and_session(
            teacher, lesson, student, enrollment,
            ExerciseCreateIn(
                exercise_type="fill_blank",
                question_text="Capital of France?",
                config={"blank_position": 0, "accepted_answers": ["Paris"]},
            ),
        )
        result = ExerciseService.submit_answer(student, ex.pk, {"text": "  paris  "})
        assert result.is_correct is True

    def test_fill_blank_incorrect(self, teacher, lesson, student, enrollment):
        ex = self._make_exercise_and_session(
            teacher, lesson, student, enrollment,
            ExerciseCreateIn(
                exercise_type="fill_blank",
                question_text="Capital of France?",
                config={"blank_position": 0, "accepted_answers": ["Paris"]},
            ),
        )
        result = ExerciseService.submit_answer(student, ex.pk, {"text": "London"})
        assert result.is_correct is False
        assert result.correct_answer == {"accepted_answers": ["Paris"]}

    def test_matching_correct(self, teacher, lesson, student, enrollment):
        ex = self._make_exercise_and_session(
            teacher, lesson, student, enrollment,
            ExerciseCreateIn(
                exercise_type="matching",
                question_text="Match",
                config={"pairs": [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]},
            ),
        )
        # Submit in different order — should still be correct
        result = ExerciseService.submit_answer(
            student, ex.pk,
            {"pairs": [{"left": "B", "right": "2"}, {"left": "A", "right": "1"}]},
        )
        assert result.is_correct is True

    def test_matching_incorrect(self, teacher, lesson, student, enrollment):
        ex = self._make_exercise_and_session(
            teacher, lesson, student, enrollment,
            ExerciseCreateIn(
                exercise_type="matching",
                question_text="Match",
                config={"pairs": [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]},
            ),
        )
        result = ExerciseService.submit_answer(
            student, ex.pk,
            {"pairs": [{"left": "A", "right": "2"}, {"left": "B", "right": "1"}]},
        )
        assert result.is_correct is False

    def test_free_text_stored_for_review(self, teacher, lesson, student, enrollment):
        ex = self._make_exercise_and_session(
            teacher, lesson, student, enrollment,
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Explain",
                config={"rubric": "Clarity"},
            ),
        )
        result = ExerciseService.submit_answer(
            student, ex.pk, {"text": "Gravity pulls things down."}
        )
        assert result.is_correct is False
        assert result.feedback == "Submitted for teacher review"
        assert result.correct_answer is None


class TestResumeLesson:
    def test_resumes_at_correct_position(self, teacher, lesson, student, enrollment):
        ex1 = ExerciseService.create_exercise(
            teacher,
            lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q1",
                config={"options": ["A", "B"], "correct_index": 0},
            ),
        )
        ex2 = ExerciseService.create_exercise(
            teacher,
            lesson.pk,
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q2",
                config={"options": ["X", "Y"], "correct_index": 1},
            ),
        )
        ExerciseService.start_lesson(student, lesson.pk)
        ExerciseService.submit_answer(student, ex1.pk, {"selected_index": 0})

        session, current = ExerciseService.resume_lesson(student, lesson.pk)
        assert current.pk == ex2.pk

    def test_no_session_raises(self, student, lesson, enrollment):
        with pytest.raises(LessonSessionNotFoundError):
            ExerciseService.resume_lesson(student, lesson.pk)

    def test_not_enrolled_raises(self, student, lesson):
        with pytest.raises(NotEnrolledError):
            ExerciseService.resume_lesson(student, lesson.pk)
