"""Exercises API routes — exercise CRUD and Duolingo-style lesson player."""

from django.http import HttpRequest
from ninja import Router

from apps.accounts.api import jwt_auth
from apps.accounts.models import Role
from apps.exercises.schemas import (
    AnswerIn,
    AnswerResult,
    ExerciseCreateIn,
    ExerciseOut,
    ExerciseUpdateIn,
    LessonSessionOut,
)
from apps.exercises.services import ExerciseService, _get_exercise_sequence
from common.permissions import require_role

router = Router(tags=["exercises"], auth=jwt_auth)


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


def _session_out(session, current_exercise) -> LessonSessionOut:
    """Build a LessonSessionOut from a LessonSession and optional Exercise."""
    total_in_sequence = len(_get_exercise_sequence(session))
    if total_in_sequence > 0:
        progress_percentage = (session.current_exercise_index / total_in_sequence) * 100
    else:
        progress_percentage = 0.0

    current_ex = None
    if current_exercise is not None:
        current_ex = ExerciseOut(
            id=current_exercise.pk,
            exercise_type=current_exercise.exercise_type,
            question_text=current_exercise.question_text,
            order=current_exercise.order,
            config=current_exercise.config,
            difficulty=current_exercise.difficulty,
            topic=current_exercise.topic,
            is_collaborative=current_exercise.is_collaborative,
            collab_group_size=current_exercise.collab_group_size,
        )

    return LessonSessionOut(
        id=session.pk,
        lesson_id=session.lesson_id,
        current_exercise=current_ex,
        progress_percentage=progress_percentage,
        is_completed=session.is_completed,
        correct_first_attempt=session.correct_first_attempt,
        total_exercises=session.total_exercises,
        retry_queue_size=len(session.retry_queue),
    )


# ------------------------------------------------------------------
# Teacher/Admin endpoints — Exercise CRUD
# ------------------------------------------------------------------


@router.post("/lessons/{lesson_id}/exercises", response={201: ExerciseOut})
@require_role(Role.TEACHER, Role.ADMIN)
def create_exercise(request: HttpRequest, lesson_id: int, payload: ExerciseCreateIn):
    """Create a new exercise in a lesson (Teacher+Admin only)."""
    exercise = ExerciseService.create_exercise(request.auth, lesson_id, payload)
    return 201, ExerciseOut(
        id=exercise.pk,
        exercise_type=exercise.exercise_type,
        question_text=exercise.question_text,
        order=exercise.order,
        config=exercise.config,
        difficulty=exercise.difficulty,
        topic=exercise.topic,
        is_collaborative=exercise.is_collaborative,
        collab_group_size=exercise.collab_group_size,
    )


@router.patch("/exercises/{exercise_id}", response=ExerciseOut)
@require_role(Role.TEACHER, Role.ADMIN)
def update_exercise(request: HttpRequest, exercise_id: int, payload: ExerciseUpdateIn):
    """Update an exercise (Teacher+Admin only)."""
    exercise = ExerciseService.update_exercise(request.auth, exercise_id, payload)
    return ExerciseOut(
        id=exercise.pk,
        exercise_type=exercise.exercise_type,
        question_text=exercise.question_text,
        order=exercise.order,
        config=exercise.config,
        difficulty=exercise.difficulty,
        topic=exercise.topic,
        is_collaborative=exercise.is_collaborative,
        collab_group_size=exercise.collab_group_size,
    )


@router.delete("/exercises/{exercise_id}", response={204: None})
@require_role(Role.TEACHER, Role.ADMIN)
def delete_exercise(request: HttpRequest, exercise_id: int):
    """Delete an exercise (Teacher+Admin only)."""
    ExerciseService.delete_exercise(request.auth, exercise_id)
    return 204, None


# ------------------------------------------------------------------
# Student endpoints — Lesson player
# ------------------------------------------------------------------


@router.get("/lessons/{lesson_id}/start", response=LessonSessionOut)
@require_role(Role.STUDENT)
def start_lesson(request: HttpRequest, lesson_id: int):
    """Start a lesson player session (Student only)."""
    session, current_exercise = ExerciseService.start_lesson(request.auth, lesson_id)
    return _session_out(session, current_exercise)


@router.post("/exercises/{exercise_id}/submit", response=AnswerResult)
@require_role(Role.STUDENT)
def submit_answer(request: HttpRequest, exercise_id: int, payload: AnswerIn):
    """Submit an answer to an exercise (Student only)."""
    return ExerciseService.submit_answer(request.auth, exercise_id, payload.answer)


@router.get("/lessons/{lesson_id}/resume", response=LessonSessionOut)
@require_role(Role.STUDENT)
def resume_lesson(request: HttpRequest, lesson_id: int):
    """Resume an existing lesson session (Student only)."""
    session, current_exercise = ExerciseService.resume_lesson(request.auth, lesson_id)
    return _session_out(session, current_exercise)
