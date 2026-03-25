"""Courses app models — Course, Unit, Lesson, Enrollment."""

from django.db import models
from django.utils import timezone as tz

from apps.accounts.models import User
from common.models import TimestampedModel


class Course(TimestampedModel):
    """Top-level content container."""

    class Status(models.TextChoices):
        DRAFT = "draft"
        PUBLISHED = "published"

    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="taught_courses"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "courses_course"

    def __str__(self) -> str:
        return self.title


class Unit(TimestampedModel):
    """Second level in Course → Unit → Lesson → Exercise hierarchy."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="units"
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()

    class Meta:
        db_table = "courses_unit"
        ordering = ["order"]
        unique_together = [("course", "order")]

    def __str__(self) -> str:
        return f"{self.course.title} — {self.title}"


class Lesson(TimestampedModel):
    """Third level. Contains exercises."""

    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()

    class Meta:
        db_table = "courses_lesson"
        ordering = ["order"]
        unique_together = [("unit", "order")]

    def __str__(self) -> str:
        return f"{self.unit.title} — {self.title}"


class Enrollment(TimestampedModel):
    """Links a Student to a Course."""

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "courses_enrollment"
        unique_together = [("student", "course")]

    def __str__(self) -> str:
        return f"{self.student.email} → {self.course.title}"
