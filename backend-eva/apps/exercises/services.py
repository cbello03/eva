"""ExerciseService — exercise CRUD and Duolingo-style lesson player logic."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.courses.models import Enrollment, Lesson
from apps.exercises.models import AnswerRecord, Exercise, LessonSession
from apps.progress.services import ProgressService
from apps.exercises.schemas import (
    AnswerResult,
    ExerciseCreateIn,
    ExerciseUpdateIn,
    _CONFIG_VALIDATORS,
)
from common.exceptions import (
    DomainError,
    InsufficientRoleError,
    NotEnrolledError,
)
from common.sanitization import sanitize_html


# ------------------------------------------------------------------
# Domain exceptions
# ------------------------------------------------------------------


class ExerciseNotFoundError(DomainError):
    status_code = 404
    code = "exercise_not_found"

    def __init__(self, detail: str = "Exercise not found"):
        super().__init__(detail)


class LessonNotFoundError(DomainError):
    status_code = 404
    code = "lesson_not_found"

    def __init__(self, detail: str = "Lesson not found"):
        super().__init__(detail)


class LessonSessionNotFoundError(DomainError):
    status_code = 404
    code = "lesson_session_not_found"

    def __init__(self, detail: str = "Lesson session not found"):
        super().__init__(detail)


class LessonAlreadyCompletedError(DomainError):
    status_code = 400
    code = "lesson_already_completed"

    def __init__(self, detail: str = "This lesson has already been completed"):
        super().__init__(detail)


class ExerciseAlreadyAnsweredError(DomainError):
    status_code = 400
    code = "exercise_already_answered"

    def __init__(self, detail: str = "This exercise is not the current one"):
        super().__init__(detail)


class InvalidExerciseConfigError(DomainError):
    status_code = 400
    code = "invalid_exercise_config"

    def __init__(self, detail: str = "Exercise configuration is invalid"):
        super().__init__(detail)


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------


def _check_lesson_owner(lesson: Lesson, user: User) -> None:
    """Raise if *user* is not the teacher who owns the course containing *lesson*."""
    course = lesson.unit.course
    if course.teacher_id != user.pk:
        raise InsufficientRoleError("You do not own this course")


def _check_enrolled(user: User, lesson: Lesson) -> None:
    """Raise if *user* is not enrolled in the course containing *lesson*."""
    course = lesson.unit.course
    if not Enrollment.objects.filter(
        student=user, course=course, is_active=True
    ).exists():
        raise NotEnrolledError()


def _get_exercise_sequence(session: LessonSession) -> list[Exercise]:
    """Return the full exercise sequence for a session.

    The sequence is: all lesson exercises in order, followed by exercises
    from the retry_queue (looked up by ID).
    """
    lesson_exercises = list(
        session.lesson.exercises.order_by("order")
    )
    if session.retry_queue:
        retry_exercises = list(
            Exercise.objects.filter(pk__in=session.retry_queue)
        )
        # Preserve retry_queue ordering
        retry_map = {e.pk: e for e in retry_exercises}
        retry_ordered = [retry_map[eid] for eid in session.retry_queue if eid in retry_map]
        return lesson_exercises + retry_ordered
    return lesson_exercises


def _get_current_exercise(session: LessonSession) -> Exercise | None:
    """Return the current exercise for the session, or None if completed."""
    sequence = _get_exercise_sequence(session)
    if session.current_exercise_index < len(sequence):
        return sequence[session.current_exercise_index]
    return None



# ------------------------------------------------------------------
# ExerciseService
# ------------------------------------------------------------------


class ExerciseService:
    """Handles exercise CRUD and Duolingo-style lesson player logic."""

    # ------------------------------------------------------------------
    # Exercise CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_exercise(teacher: User, lesson_id: int, data: ExerciseCreateIn) -> Exercise:
        """Create a new exercise in a lesson."""
        try:
            lesson = Lesson.objects.select_related("unit__course").get(pk=lesson_id)
        except Lesson.DoesNotExist:
            raise LessonNotFoundError()

        _check_lesson_owner(lesson, teacher)

        order = lesson.exercises.count() + 1

        return Exercise.objects.create(
            lesson=lesson,
            exercise_type=data.exercise_type,
            question_text=sanitize_html(data.question_text),
            order=order,
            config=data.config,
            difficulty=data.difficulty,
            topic=data.topic,
            is_collaborative=data.is_collaborative,
            collab_group_size=data.collab_group_size,
        )

    @staticmethod
    def update_exercise(teacher: User, exercise_id: int, data: ExerciseUpdateIn) -> Exercise:
        """Update an exercise. Only non-None fields are changed."""
        try:
            exercise = Exercise.objects.select_related(
                "lesson__unit__course"
            ).get(pk=exercise_id)
        except Exercise.DoesNotExist:
            raise ExerciseNotFoundError()

        _check_lesson_owner(exercise.lesson, teacher)

        if data.question_text is not None:
            exercise.question_text = sanitize_html(data.question_text)
        if data.config is not None:
            # Validate config against the exercise's type
            validator_cls = _CONFIG_VALIDATORS.get(exercise.exercise_type)
            if validator_cls is not None:
                validator_cls(**data.config)
            exercise.config = data.config
        if data.difficulty is not None:
            exercise.difficulty = data.difficulty
        if data.topic is not None:
            exercise.topic = data.topic
        if data.is_collaborative is not None:
            exercise.is_collaborative = data.is_collaborative
        if data.collab_group_size is not None:
            exercise.collab_group_size = data.collab_group_size

        exercise.save()
        return exercise

    @staticmethod
    def delete_exercise(teacher: User, exercise_id: int) -> None:
        """Delete an exercise and re-number remaining exercises."""
        try:
            exercise = Exercise.objects.select_related(
                "lesson__unit__course"
            ).get(pk=exercise_id)
        except Exercise.DoesNotExist:
            raise ExerciseNotFoundError()

        _check_lesson_owner(exercise.lesson, teacher)
        lesson = exercise.lesson

        with transaction.atomic():
            exercise.delete()
            # Re-number remaining exercises to maintain contiguous order
            remaining = lesson.exercises.order_by("order")
            for new_order, ex in enumerate(remaining, start=1):
                if ex.order != new_order:
                    Exercise.objects.filter(pk=ex.pk).update(order=new_order)

    # ------------------------------------------------------------------
    # Lesson player
    # ------------------------------------------------------------------

    @staticmethod
    def start_lesson(student: User, lesson_id: int) -> tuple[LessonSession, Exercise | None]:
        """Start or resume a lesson session. Returns (session, current_exercise)."""
        try:
            lesson = Lesson.objects.select_related("unit__course").get(pk=lesson_id)
        except Lesson.DoesNotExist:
            raise LessonNotFoundError()

        _check_enrolled(student, lesson)

        # Check for existing session
        existing = LessonSession.objects.filter(
            student=student, lesson=lesson
        ).first()

        if existing is not None:
            if existing.is_completed:
                raise LessonAlreadyCompletedError()
            # Resume: return existing session with current exercise
            current = _get_current_exercise(existing)
            return existing, current

        # Create new session
        total = lesson.exercises.count()
        session = LessonSession.objects.create(
            student=student,
            lesson=lesson,
            total_exercises=total,
        )
        first_exercise = lesson.exercises.order_by("order").first()
        return session, first_exercise

    @staticmethod
    def submit_answer(student: User, exercise_id: int, answer: dict) -> AnswerResult:
        """Submit an answer to an exercise and return feedback."""
        try:
            exercise = Exercise.objects.select_related(
                "lesson__unit__course"
            ).get(pk=exercise_id)
        except Exercise.DoesNotExist:
            raise ExerciseNotFoundError()

        _check_enrolled(student, exercise.lesson)

        # Get active session
        try:
            session = LessonSession.objects.get(
                student=student,
                lesson=exercise.lesson,
                is_completed=False,
            )
        except LessonSession.DoesNotExist:
            raise LessonSessionNotFoundError()

        # Verify this is the current exercise
        current = _get_current_exercise(session)
        if current is None or current.pk != exercise.pk:
            raise ExerciseAlreadyAnsweredError()

        # Check if this is the first attempt for this exercise in this session
        is_first = not AnswerRecord.objects.filter(
            student=student,
            exercise=exercise,
            session=session,
            is_first_attempt=True,
        ).exists()

        # Evaluate answer based on exercise type
        is_correct, correct_answer, feedback = _evaluate_answer(
            exercise, answer
        )

        # Create answer record
        AnswerRecord.objects.create(
            student=student,
            exercise=exercise,
            session=session,
            submitted_answer=answer,
            is_correct=is_correct,
            is_first_attempt=is_first,
        )

        # Update session state
        if is_correct and is_first:
            session.correct_first_attempt += 1

        if not is_correct and exercise.exercise_type != "free_text":
            # Add to retry queue if not already there
            if exercise.pk not in session.retry_queue:
                session.retry_queue = session.retry_queue + [exercise.pk]

        # Advance to next exercise
        session.current_exercise_index += 1

        # Check completion
        sequence = _get_exercise_sequence(session)
        if session.current_exercise_index >= len(sequence):
            session.is_completed = True
            session.completed_at = tz.now()
            lesson_exercises = list(session.lesson.exercises.values_list("pk", flat=True))
            total_lesson_exercises = len(lesson_exercises)
            correct_lesson_answers = AnswerRecord.objects.filter(
                student=student,
                session=session,
                exercise_id__in=lesson_exercises,
                is_correct=True,
            ).count()
            lesson_score = (
                (correct_lesson_answers / total_lesson_exercises) * 100.0
                if total_lesson_exercises > 0
                else 0.0
            )
            ProgressService.update_lesson_progress(
                student=student,
                lesson_id=session.lesson_id,
                score=lesson_score,
            )
            # Keep gamification/activity updates best-effort so lesson flow
            # cannot fail if auxiliary systems have transient issues.
            try:
                from apps.gamification.services import GamificationService

                xp_earned = 50 + int(round(lesson_score / 2))
                GamificationService.award_xp(
                    student=student,
                    source_type="lesson",
                    source_id=session.lesson_id,
                    amount=xp_earned,
                )
                GamificationService.update_streak(student)
                ProgressService.record_daily_activity(
                    student=student,
                    lessons_completed=1,
                    xp_earned=xp_earned,
                )
            except Exception:
                pass

        session.save()

        return AnswerResult(
            is_correct=is_correct,
            correct_answer=correct_answer,
            feedback=feedback,
        )

    @staticmethod
    def resume_lesson(student: User, lesson_id: int) -> tuple[LessonSession, Exercise | None]:
        """Resume an existing lesson session."""
        try:
            lesson = Lesson.objects.select_related("unit__course").get(pk=lesson_id)
        except Lesson.DoesNotExist:
            raise LessonNotFoundError()

        _check_enrolled(student, lesson)

        try:
            session = LessonSession.objects.get(
                student=student, lesson=lesson
            )
        except LessonSession.DoesNotExist:
            raise LessonSessionNotFoundError()

        current = _get_current_exercise(session)
        return session, current


# ------------------------------------------------------------------
# Answer evaluation
# ------------------------------------------------------------------


def _evaluate_answer(
    exercise: Exercise, answer: dict
) -> tuple[bool, dict | None, str]:
    """Evaluate an answer and return (is_correct, correct_answer, feedback).

    *correct_answer* is populated only when the answer is wrong and the
    exercise is auto-graded.
    """
    etype = exercise.exercise_type
    config = exercise.config

    if etype == "multiple_choice":
        selected = answer.get("selected_index")
        options = config.get("options", [])
        correct_idx = config.get("correct_index")

        # Backward compatibility: support seeded configs with
        # {"options":[{"id","text"}...], "correct":"<id>"}.
        if correct_idx is None:
            correct_id = config.get("correct")
            if correct_id is not None and isinstance(options, list):
                for idx, option in enumerate(options):
                    if isinstance(option, dict) and option.get("id") == correct_id:
                        correct_idx = idx
                        break

        if not isinstance(correct_idx, int):
            raise InvalidExerciseConfigError(
                "Multiple choice config must include valid 'correct_index' or 'correct' option id"
            )

        is_correct = selected == correct_idx
        correct_answer = None if is_correct else {"selected_index": correct_idx}
        feedback = "Correct!" if is_correct else "Incorrect."
        return is_correct, correct_answer, feedback

    if etype == "fill_blank":
        submitted_text = str(answer.get("text", "")).strip().lower()
        accepted_answers = config.get("accepted_answers")

        # Backward compatibility: support seeded configs with
        # {"blanks":[{"id":"...","correct":"..."}]}.
        if accepted_answers is None:
            blanks = config.get("blanks", [])
            if isinstance(blanks, list):
                accepted_answers = [
                    blank.get("correct")
                    for blank in blanks
                    if isinstance(blank, dict) and blank.get("correct")
                ]

        if not isinstance(accepted_answers, list) or len(accepted_answers) == 0:
            raise InvalidExerciseConfigError(
                "Fill blank config must include non-empty 'accepted_answers' or legacy 'blanks'"
            )

        accepted = [str(a).strip().lower() for a in accepted_answers]
        is_correct = submitted_text in accepted
        correct_answer = None if is_correct else {"accepted_answers": accepted_answers}
        feedback = "Correct!" if is_correct else "Incorrect."
        return is_correct, correct_answer, feedback

    if etype == "matching":
        submitted_pairs = answer.get("pairs", [])
        correct_pairs = config["pairs"]
        # Order-independent comparison: normalize to sets of (left, right) tuples
        submitted_set = {(p.get("left"), p.get("right")) for p in submitted_pairs}
        correct_set = {(p["left"], p["right"]) for p in correct_pairs}
        is_correct = submitted_set == correct_set
        correct_answer = None if is_correct else {"pairs": correct_pairs}
        feedback = "Correct!" if is_correct else "Incorrect."
        return is_correct, correct_answer, feedback

    if etype == "free_text":
        # Free text: always store for teacher review
        return False, None, "Submitted for teacher review"

    # Fallback (should not happen with validated exercise types)
    return False, None, "Unknown exercise type"
