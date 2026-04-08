"""Progress app models — CourseProgress, LessonProgress, DailyActivity, TopicMastery, SpacedRepetitionItem."""

from django.db import models

from apps.accounts.models import User
from apps.courses.models import Course, Lesson
from apps.exercises.models import Exercise
from common.models import TimestampedModel


class CourseProgress(TimestampedModel):
    """Tracks a student's progress through a course."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="course_progress"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="student_progress"
    )
    completion_percentage = models.FloatField(default=0.0)
    total_score = models.FloatField(default=0.0)
    lessons_completed = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "progress_courseprogress"
        unique_together = [("student", "course")]

    def __str__(self) -> str:
        return f"{self.student.email} — {self.course.title} ({self.completion_percentage:.1f}%)"


class LessonProgress(TimestampedModel):
    """Tracks completion and score per lesson."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="student_progress"
    )
    is_completed = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)  # Percentage correct
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "progress_lessonprogress"
        unique_together = [("student", "lesson")]

    def __str__(self) -> str:
        return f"{self.student.email} — {self.lesson.title} ({'✓' if self.is_completed else '○'})"


class DailyActivity(TimestampedModel):
    """Tracks daily learning activity for heatmap display."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_activities"
    )
    date = models.DateField()
    lessons_completed = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    time_spent_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "progress_dailyactivity"
        unique_together = [("student", "date")]

    def __str__(self) -> str:
        return f"{self.student.email} — {self.date} ({self.lessons_completed} lessons)"


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
