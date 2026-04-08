"""Progress app models — TopicMastery, SpacedRepetitionItem."""

from django.db import models

from apps.accounts.models import User
from apps.courses.models import Course
from apps.exercises.models import Exercise
from common.models import TimestampedModel


class TopicMastery(TimestampedModel):
    """Adaptive learning: mastery score per topic per student."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="topic_mastery"
    )
    topic = models.CharField(max_length=100)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="topic_mastery"
    )
    correct_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    mastery_score = models.FloatField(default=0.0)  # Weighted by recency
    last_reviewed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "progress_topicmastery"
        unique_together = [("student", "topic", "course")]

    def __str__(self) -> str:
        return f"{self.student.email} — {self.topic} ({self.course.title})"


class SpacedRepetitionItem(TimestampedModel):
    """Schedules review exercises using spaced repetition intervals."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="spaced_items"
    )
    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="spaced_items"
    )
    next_review_date = models.DateField()
    interval_days = models.PositiveIntegerField(default=1)  # Current interval: 1, 3, 7, 14, 30
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "progress_spacedrepetitionitem"

    def __str__(self) -> str:
        return f"{self.student.email} — Exercise {self.exercise_id} (next: {self.next_review_date})"
