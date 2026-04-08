"""AdaptiveService — mastery tracking, spaced repetition, difficulty adjustment."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from django.db.models import QuerySet
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.courses.models import Unit
from apps.exercises.models import AnswerRecord, Exercise
from apps.progress.models import SpacedRepetitionItem, TopicMastery


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

# Recency weight — how much the latest answer influences the score
ALPHA = 0.3

# Mastery threshold below which review is recommended
MASTERY_THRESHOLD = 0.6

# Maximum exercises returned in a review session
MAX_REVIEW_EXERCISES = 10

# Spaced repetition interval progression (in days)
SPACED_INTERVALS = [1, 3, 7, 14, 30]

# Difficulty bounds
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5

# Consecutive answer thresholds for difficulty adjustment
CONSECUTIVE_CORRECT_THRESHOLD = 3
CONSECUTIVE_INCORRECT_THRESHOLD = 2


# ------------------------------------------------------------------
# DTOs
# ------------------------------------------------------------------


@dataclass
class ReviewRecommendation:
    """Returned by should_recommend_review when weak topics exist."""

    should_review: bool
    weak_topics: list[dict]  # [{"topic": str, "mastery_score": float}, ...]


# ------------------------------------------------------------------
# AdaptiveService
# ------------------------------------------------------------------


class AdaptiveService:
    """Handles adaptive learning: mastery scores, review recommendations,
    spaced repetition scheduling, and difficulty adjustment."""

    @staticmethod
    def record_answer(student: User, exercise: Exercise, is_correct: bool) -> None:
        """Update TopicMastery for the exercise's topic.

        Increments correct_count / total_count and recalculates mastery_score
        using exponential recency weighting:
            new_score = alpha * (1 if correct else 0) + (1 - alpha) * old_score
        """
        topic = exercise.topic
        if not topic:
            return  # No topic tagged — nothing to track

        course = exercise.lesson.unit.course

        mastery, _created = TopicMastery.objects.get_or_create(
            student=student,
            topic=topic,
            course=course,
        )

        mastery.total_count += 1
        if is_correct:
            mastery.correct_count += 1

        # Recency-weighted mastery score
        mastery.mastery_score = (
            ALPHA * (1.0 if is_correct else 0.0)
            + (1 - ALPHA) * mastery.mastery_score
        )
        mastery.last_reviewed = tz.now()
        mastery.save(
            update_fields=[
                "correct_count",
                "total_count",
                "mastery_score",
                "last_reviewed",
                "updated_at",
            ]
        )

    @staticmethod
    def get_mastery_scores(student: User, course_id: int) -> dict[str, float]:
        """Return mastery scores per topic for a student in a course.

        Returns a dict mapping topic name → mastery_score.
        """
        qs: QuerySet[TopicMastery] = TopicMastery.objects.filter(
            student=student,
            course_id=course_id,
        )
        return {tm.topic: tm.mastery_score for tm in qs}

    @staticmethod
    def should_recommend_review(
        student: User, unit_id: int
    ) -> ReviewRecommendation:
        """Check if any topic for exercises in a unit has mastery_score < 0.6.

        Returns a ReviewRecommendation with weak topics sorted by mastery
        score ascending.
        """
        try:
            unit = Unit.objects.select_related("course").get(pk=unit_id)
        except Unit.DoesNotExist:
            return ReviewRecommendation(should_review=False, weak_topics=[])

        course = unit.course

        # Collect distinct topics from exercises in this unit's lessons
        topics_in_unit: set[str] = set(
            Exercise.objects.filter(
                lesson__unit=unit,
            )
            .exclude(topic="")
            .values_list("topic", flat=True)
            .distinct()
        )

        if not topics_in_unit:
            return ReviewRecommendation(should_review=False, weak_topics=[])

        # Get mastery records for those topics
        mastery_records = TopicMastery.objects.filter(
            student=student,
            course=course,
            topic__in=topics_in_unit,
        )
        mastery_map = {tm.topic: tm.mastery_score for tm in mastery_records}

        weak_topics: list[dict] = []
        for topic in topics_in_unit:
            score = mastery_map.get(topic, 0.0)  # No record → 0.0
            if score < MASTERY_THRESHOLD:
                weak_topics.append({"topic": topic, "mastery_score": score})

        # Sort by mastery score ascending (weakest first)
        weak_topics.sort(key=lambda t: t["mastery_score"])

        return ReviewRecommendation(
            should_review=len(weak_topics) > 0,
            weak_topics=weak_topics,
        )

    @staticmethod
    def generate_review_session(
        student: User, course_id: int
    ) -> list[Exercise]:
        """Select exercises from weak topics, prioritising lowest mastery scores.

        Returns up to MAX_REVIEW_EXERCISES exercises.
        """
        weak_mastery = (
            TopicMastery.objects.filter(
                student=student,
                course_id=course_id,
                mastery_score__lt=MASTERY_THRESHOLD,
            )
            .order_by("mastery_score")
        )

        if not weak_mastery.exists():
            return []

        # Collect exercises from weak topics, ordered by mastery (weakest first)
        exercises: list[Exercise] = []
        for tm in weak_mastery:
            if len(exercises) >= MAX_REVIEW_EXERCISES:
                break
            topic_exercises = list(
                Exercise.objects.filter(
                    lesson__unit__course_id=course_id,
                    topic=tm.topic,
                ).order_by("?")[: MAX_REVIEW_EXERCISES - len(exercises)]
            )
            exercises.extend(topic_exercises)

        return exercises[:MAX_REVIEW_EXERCISES]

    @staticmethod
    def schedule_spaced_repetition(
        student: User, exercise: Exercise, is_correct: bool
    ) -> None:
        """Schedule or update spaced repetition for an exercise.

        On incorrect answer: create/reset SpacedRepetitionItem with
            interval_days=1, next_review_date = today + 1 day.
        On correct review: advance interval through [1, 3, 7, 14, 30].
        """
        today = datetime.date.today()

        existing = SpacedRepetitionItem.objects.filter(
            student=student,
            exercise=exercise,
        ).first()

        if not is_correct:
            # Incorrect answer → create or reset to interval 1
            if existing:
                existing.interval_days = SPACED_INTERVALS[0]
                existing.next_review_date = today + datetime.timedelta(days=1)
                existing.save(
                    update_fields=[
                        "interval_days",
                        "next_review_date",
                        "updated_at",
                    ]
                )
            else:
                SpacedRepetitionItem.objects.create(
                    student=student,
                    exercise=exercise,
                    interval_days=SPACED_INTERVALS[0],
                    next_review_date=today + datetime.timedelta(days=1),
                    review_count=0,
                )
        else:
            # Correct review → advance to next interval
            if existing:
                current_interval = existing.interval_days
                try:
                    idx = SPACED_INTERVALS.index(current_interval)
                    next_idx = min(idx + 1, len(SPACED_INTERVALS) - 1)
                except ValueError:
                    # Current interval not in list — start from beginning
                    next_idx = 0

                next_interval = SPACED_INTERVALS[next_idx]
                existing.interval_days = next_interval
                existing.next_review_date = today + datetime.timedelta(
                    days=next_interval
                )
                existing.review_count += 1
                existing.save(
                    update_fields=[
                        "interval_days",
                        "next_review_date",
                        "review_count",
                        "updated_at",
                    ]
                )
            # If no existing item and answer is correct, nothing to schedule

    @staticmethod
    def adjust_difficulty(student: User, exercise: Exercise) -> int:
        """Suggest a difficulty level based on recent consecutive answers.

        After 3 consecutive correct → increase difficulty (max 5).
        After 2 consecutive incorrect → decrease difficulty (max 1).
        Returns the suggested difficulty level.
        """
        # Get the most recent answers for this student, ordered newest first
        recent_answers = list(
            AnswerRecord.objects.filter(
                student=student,
                exercise__lesson=exercise.lesson,
            )
            .order_by("-answered_at")
            .values_list("is_correct", flat=True)[
                : max(CONSECUTIVE_CORRECT_THRESHOLD, CONSECUTIVE_INCORRECT_THRESHOLD)
            ]
        )

        current_difficulty = exercise.difficulty

        if not recent_answers:
            return current_difficulty

        # Check for consecutive correct answers
        if len(recent_answers) >= CONSECUTIVE_CORRECT_THRESHOLD:
            if all(recent_answers[:CONSECUTIVE_CORRECT_THRESHOLD]):
                return min(current_difficulty + 1, MAX_DIFFICULTY)

        # Check for consecutive incorrect answers
        if len(recent_answers) >= CONSECUTIVE_INCORRECT_THRESHOLD:
            if not any(recent_answers[:CONSECUTIVE_INCORRECT_THRESHOLD]):
                return max(current_difficulty - 1, MIN_DIFFICULTY)

        return current_difficulty
