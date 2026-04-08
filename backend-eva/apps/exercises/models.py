"""Exercises app models — Exercise, LessonSession, AnswerRecord."""

from django.db import models

from apps.accounts.models import User
from apps.courses.models import Lesson
from common.models import TimestampedModel


class ExerciseType(models.TextChoices):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    FREE_TEXT = "free_text"


class Exercise(TimestampedModel):
    """An exercise within a lesson."""

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="exercises"
    )
    exercise_type = models.CharField(
        max_length=20, choices=ExerciseType.choices
    )
    question_text = models.TextField()
    order = models.PositiveIntegerField()
    config = models.JSONField()
    difficulty = models.PositiveSmallIntegerField(default=1)
    topic = models.CharField(max_length=100, blank=True)
    is_collaborative = models.BooleanField(default=False)
    collab_group_size = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "exercises_exercise"
        ordering = ["order"]
        unique_together = [("lesson", "order")]

    def __str__(self) -> str:
        return f"{self.lesson.title} — Exercise {self.order}"


class LessonSession(TimestampedModel):
    """Tracks a student's progress through a lesson."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="lesson_sessions"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="sessions"
    )
    current_exercise_index = models.PositiveIntegerField(default=0)
    retry_queue = models.JSONField(default=list)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    correct_first_attempt = models.PositiveIntegerField(default=0)
    total_exercises = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "exercises_lesson_session"
        unique_together = [("student", "lesson")]

    def __str__(self) -> str:
        return f"{self.student.email} — {self.lesson.title}"


class AnswerRecord(TimestampedModel):
    """Records a student's answer to an exercise."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="answers"
    )
    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="answers"
    )
    session = models.ForeignKey(
        LessonSession, on_delete=models.CASCADE, related_name="answers"
    )
    submitted_answer = models.JSONField()
    is_correct = models.BooleanField()
    is_first_attempt = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exercises_answer_record"

    def __str__(self) -> str:
        return f"{self.student.email} — Exercise {self.exercise_id}"
