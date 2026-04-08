"""Unit tests for ProgressService."""

import datetime
import uuid

import pytest
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.gamification.models import GamificationProfile
from apps.progress.models import (
    CourseProgress,
    DailyActivity,
    LessonProgress,
    TopicMastery,
)
from apps.progress.services import ProgressService

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _make_user() -> User:
    uid = _uid()
    return User.objects.create_user(
        username=f"student_{uid}",
        email=f"student_{uid}@test.com",
        password="Test1234",
        display_name="Test Student",
        role="student",
    )


def _make_teacher() -> User:
    uid = _uid()
    return User.objects.create_user(
        username=f"teacher_{uid}",
        email=f"teacher_{uid}@test.com",
        password="Test1234",
        display_name="Test Teacher",
        role="teacher",
    )


def _make_course_with_lessons(
    teacher: User, num_units: int = 2, lessons_per_unit: int = 2
) -> Course:
    """Create a published course with units and lessons."""
    course = Course.objects.create(
        title="Test Course",
        description="A test course",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )
    for u_idx in range(1, num_units + 1):
        unit = Unit.objects.create(course=course, title=f"Unit {u_idx}", order=u_idx)
        for l_idx in range(1, lessons_per_unit + 1):
            Lesson.objects.create(unit=unit, title=f"Lesson {u_idx}.{l_idx}", order=l_idx)
    return course


# ---------------------------------------------------------------------------
# initialize_course_progress
# ---------------------------------------------------------------------------


class TestInitializeCourseProgress:
    def test_creates_course_progress_and_lesson_progress(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=2, lessons_per_unit=3)

        cp = ProgressService.initialize_course_progress(student, course.pk)

        assert cp.student == student
        assert cp.course == course
        assert cp.total_lessons == 6
        assert cp.completion_percentage == 0.0
        assert LessonProgress.objects.filter(student=student).count() == 6

    def test_idempotent_on_second_call(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=2)

        ProgressService.initialize_course_progress(student, course.pk)
        ProgressService.initialize_course_progress(student, course.pk)

        assert CourseProgress.objects.filter(student=student, course=course).count() == 1
        assert LessonProgress.objects.filter(student=student).count() == 2

    def test_updates_total_lessons_on_reinit(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)

        ProgressService.initialize_course_progress(student, course.pk)
        # Add another lesson
        unit = course.units.first()
        Lesson.objects.create(unit=unit, title="New Lesson", order=2)

        cp = ProgressService.initialize_course_progress(student, course.pk)
        assert cp.total_lessons == 2

    def test_empty_course_creates_progress_with_zero_lessons(self):
        teacher = _make_teacher()
        student = _make_user()
        course = Course.objects.create(
            title="Empty Course",
            description="No units",
            teacher=teacher,
            status=Course.Status.PUBLISHED,
        )

        cp = ProgressService.initialize_course_progress(student, course.pk)

        assert cp.total_lessons == 0
        assert cp.completion_percentage == 0.0
        assert LessonProgress.objects.filter(student=student).count() == 0


# ---------------------------------------------------------------------------
# update_lesson_progress
# ---------------------------------------------------------------------------


class TestUpdateLessonProgress:
    def test_marks_lesson_completed_and_updates_course(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=2)
        ProgressService.initialize_course_progress(student, course.pk)

        lessons = list(Lesson.objects.filter(unit__course=course).order_by("pk"))
        lp = ProgressService.update_lesson_progress(student, lessons[0].pk, 85.0)

        assert lp.is_completed is True
        assert lp.score == 85.0
        assert lp.completed_at is not None

        cp = CourseProgress.objects.get(student=student, course=course)
        assert cp.lessons_completed == 1
        assert cp.completion_percentage == 50.0
        assert cp.total_score == 85.0

    def test_completing_all_lessons_reaches_100_percent(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=2)
        ProgressService.initialize_course_progress(student, course.pk)

        lessons = list(Lesson.objects.filter(unit__course=course).order_by("pk"))
        ProgressService.update_lesson_progress(student, lessons[0].pk, 80.0)
        ProgressService.update_lesson_progress(student, lessons[1].pk, 100.0)

        cp = CourseProgress.objects.get(student=student, course=course)
        assert cp.lessons_completed == 2
        assert cp.completion_percentage == 100.0
        assert cp.total_score == 90.0  # avg of 80 and 100

    def test_works_without_prior_initialization(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)

        lesson = Lesson.objects.filter(unit__course=course).first()
        lp = ProgressService.update_lesson_progress(student, lesson.pk, 75.0)

        assert lp.is_completed is True
        cp = CourseProgress.objects.get(student=student, course=course)
        assert cp.completion_percentage == 100.0

    def test_rescoring_lesson_updates_average(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=2)
        ProgressService.initialize_course_progress(student, course.pk)

        lessons = list(Lesson.objects.filter(unit__course=course).order_by("pk"))
        ProgressService.update_lesson_progress(student, lessons[0].pk, 60.0)
        ProgressService.update_lesson_progress(student, lessons[1].pk, 80.0)

        # Re-score first lesson with higher score
        ProgressService.update_lesson_progress(student, lessons[0].pk, 100.0)

        cp = CourseProgress.objects.get(student=student, course=course)
        assert cp.total_score == 90.0  # avg of 100 and 80


# ---------------------------------------------------------------------------
# get_dashboard
# ---------------------------------------------------------------------------


class TestGetDashboard:
    def test_returns_defaults_for_new_student(self):
        student = _make_user()
        data = ProgressService.get_dashboard(student)

        assert data.total_xp == 0
        assert data.current_level == 1
        assert data.current_streak == 0
        assert data.courses_enrolled == 0
        assert data.courses_completed == 0

    def test_returns_gamification_data(self):
        student = _make_user()
        GamificationProfile.objects.create(
            student=student, total_xp=500, current_level=3, current_streak=5
        )

        data = ProgressService.get_dashboard(student)
        assert data.total_xp == 500
        assert data.current_level == 3
        assert data.current_streak == 5

    def test_counts_enrolled_and_completed_courses(self):
        teacher = _make_teacher()
        student = _make_user()

        c1 = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)
        c2 = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)
        c2.title = "Course 2"
        c2.save()

        Enrollment.objects.create(student=student, course=c1)
        Enrollment.objects.create(student=student, course=c2)

        # Complete c1
        CourseProgress.objects.create(
            student=student, course=c1, completion_percentage=100.0, total_lessons=1, lessons_completed=1
        )
        CourseProgress.objects.create(
            student=student, course=c2, completion_percentage=50.0, total_lessons=1
        )

        data = ProgressService.get_dashboard(student)
        assert data.courses_enrolled == 2
        assert data.courses_completed == 1

    def test_excludes_inactive_enrollments_from_count(self):
        teacher = _make_teacher()
        student = _make_user()

        c1 = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)
        c2 = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)

        Enrollment.objects.create(student=student, course=c1, is_active=True)
        Enrollment.objects.create(student=student, course=c2, is_active=False)

        data = ProgressService.get_dashboard(student)
        assert data.courses_enrolled == 1


# ---------------------------------------------------------------------------
# get_course_progress
# ---------------------------------------------------------------------------


class TestGetCourseProgress:
    def test_returns_per_unit_per_lesson_data(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=2, lessons_per_unit=2)
        ProgressService.initialize_course_progress(student, course.pk)

        # Complete one lesson
        lesson = Lesson.objects.filter(unit__course=course).first()
        ProgressService.update_lesson_progress(student, lesson.pk, 90.0)

        data = ProgressService.get_course_progress(student, course.pk)

        assert data.course_id == course.pk
        assert data.course_title == course.title
        assert data.lessons_completed == 1
        assert data.total_lessons == 4
        assert len(data.units) == 2
        assert len(data.units[0].lessons) == 2
        assert len(data.units[1].lessons) == 2

    def test_returns_empty_progress_for_unenrolled(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)

        data = ProgressService.get_course_progress(student, course.pk)
        assert data.completion_percentage == 0.0
        assert data.lessons_completed == 0


# ---------------------------------------------------------------------------
# get_activity_heatmap
# ---------------------------------------------------------------------------


class TestGetActivityHeatmap:
    def test_returns_90_days_with_zeros_for_missing(self):
        student = _make_user()
        result = ProgressService.get_activity_heatmap(student, days=90)

        assert len(result) == 90
        assert all(d.lessons_completed == 0 for d in result)
        assert all(d.xp_earned == 0 for d in result)

    def test_fills_existing_activity_data(self):
        student = _make_user()
        today = tz.localdate()
        DailyActivity.objects.create(
            student=student, date=today, lessons_completed=3, xp_earned=150, time_spent_minutes=45
        )

        result = ProgressService.get_activity_heatmap(student, days=7)

        assert len(result) == 7
        last_day = result[-1]
        assert last_day.date == today
        assert last_day.lessons_completed == 3
        assert last_day.xp_earned == 150
        assert last_day.time_spent_minutes == 45

    def test_custom_days_parameter(self):
        student = _make_user()
        result = ProgressService.get_activity_heatmap(student, days=30)
        assert len(result) == 30

    def test_multiple_activity_days_interleaved(self):
        student = _make_user()
        today = tz.localdate()
        DailyActivity.objects.create(
            student=student, date=today - datetime.timedelta(days=2),
            lessons_completed=1, xp_earned=50, time_spent_minutes=20,
        )
        DailyActivity.objects.create(
            student=student, date=today,
            lessons_completed=2, xp_earned=100, time_spent_minutes=40,
        )

        result = ProgressService.get_activity_heatmap(student, days=5)

        assert len(result) == 5
        # Day at index 2 (today - 2) should have data
        day_minus_2 = next(d for d in result if d.date == today - datetime.timedelta(days=2))
        assert day_minus_2.lessons_completed == 1
        # Day at index 3 (today - 1) should be zero-filled
        day_minus_1 = next(d for d in result if d.date == today - datetime.timedelta(days=1))
        assert day_minus_1.lessons_completed == 0
        # Today should have data
        day_today = next(d for d in result if d.date == today)
        assert day_today.lessons_completed == 2


# ---------------------------------------------------------------------------
# get_mastery_scores
# ---------------------------------------------------------------------------


class TestGetMasteryScores:
    def test_returns_empty_for_new_student(self):
        student = _make_user()
        result = ProgressService.get_mastery_scores(student)
        assert result == []

    def test_returns_topic_mastery_data(self):
        teacher = _make_teacher()
        student = _make_user()
        course = _make_course_with_lessons(teacher, num_units=1, lessons_per_unit=1)

        now = tz.now()
        TopicMastery.objects.create(
            student=student, topic="algebra", course=course,
            correct_count=8, total_count=10, mastery_score=0.8, last_reviewed=now,
        )
        TopicMastery.objects.create(
            student=student, topic="geometry", course=course,
            correct_count=3, total_count=10, mastery_score=0.3, last_reviewed=now,
        )

        result = ProgressService.get_mastery_scores(student)

        assert len(result) == 2
        assert result[0].topic == "algebra"
        assert result[0].mastery_score == 0.8
        assert result[1].topic == "geometry"
        assert result[1].mastery_score == 0.3
