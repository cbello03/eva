"""Progress app Pydantic schemas for request/response validation."""

from __future__ import annotations

import datetime

from ninja import Schema


# ---------------------------------------------------------------------------
# Student progress schemas
# ---------------------------------------------------------------------------


class DashboardOut(Schema):
    """Overall student dashboard stats (Requirement 20.1)."""

    total_xp: int
    current_level: int
    current_streak: int
    courses_enrolled: int
    courses_completed: int


class LessonProgressOut(Schema):
    """Per-lesson completion and score."""

    lesson_id: int
    lesson_title: str
    is_completed: bool
    score: float


class UnitProgressOut(Schema):
    """Per-unit progress with nested lessons."""

    unit_id: int
    unit_title: str
    lessons: list[LessonProgressOut]


class CourseProgressOut(Schema):
    """Per-course progress detail (Requirement 20.2)."""

    course_id: int
    course_title: str
    completion_percentage: float
    total_score: float
    lessons_completed: int
    total_lessons: int
    units: list[UnitProgressOut]


class ActivityDayOut(Schema):
    """Single day in the activity heatmap (Requirement 20.4)."""

    date: datetime.date
    lessons_completed: int
    xp_earned: int
    time_spent_minutes: int


class MasteryScoreOut(Schema):
    """Topic mastery score (Requirement 20.3)."""

    topic: str
    correct_count: int
    total_count: int
    mastery_score: float
    last_reviewed: datetime.datetime | None


# ---------------------------------------------------------------------------
# Teacher analytics schemas
# ---------------------------------------------------------------------------


class CourseAnalyticsOut(Schema):
    """Aggregate course stats for teacher (Requirement 16.1)."""

    course_id: int
    total_enrolled: int
    average_completion_rate: float
    average_score: float
    average_time_per_lesson: float


class StudentListEntryOut(Schema):
    """Per-student row in teacher's student list (Requirement 16.2)."""

    student_id: int
    email: str
    display_name: str
    progress_percentage: float
    score: float
    streak: int
    last_activity: datetime.date | None


class TeacherLessonDetailOut(Schema):
    """Per-lesson detail in teacher's student detail view."""

    lesson_id: int
    lesson_title: str
    is_completed: bool
    score: float


class TeacherUnitDetailOut(Schema):
    """Per-unit detail in teacher's student detail view."""

    unit_id: int
    unit_title: str
    lessons: list[TeacherLessonDetailOut]


class StudentDetailOut(Schema):
    """Detailed student progress for teacher (Requirement 16.3)."""

    student_id: int
    email: str
    display_name: str
    completion_percentage: float
    total_score: float
    units: list[TeacherUnitDetailOut]


class TopicAccuracyOut(Schema):
    """Exercise accuracy per topic for heatmap (Requirement 16.4)."""

    topic: str
    total_answers: int
    correct_answers: int
    accuracy: float
