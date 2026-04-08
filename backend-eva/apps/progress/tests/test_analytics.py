"""Unit tests for AnalyticsService."""

import uuid

import pytest
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import AnswerRecord, Exercise, LessonSession
from apps.gamification.models import GamificationProfile
from apps.progress.analytics import AnalyticsService
from apps.progress.models import CourseProgress, DailyActivity, LessonProgress

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _make_user(**kwargs) -> User:
    uid = _uid()
    defaults = dict(
        username=f"student_{uid}",
        email=f"student_{uid}@test.com",
        password="Test1234",
        display_name="Test Student",
        role="student",
    )
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def _make_teacher() -> User:
    uid = _uid()
    return User.objects.create_user(
        username=f"teacher_{uid}",
        email=f"teacher_{uid}@test.com",
        password="Test1234",
        display_name="Test Teacher",
        role="teacher",
    )


def _make_course(teacher: User, num_units: int = 2, lessons_per_unit: int = 2) -> Course:
    uid = _uid()
    course = Course.objects.create(
        title=f"Course {uid}",
        description="A test course",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )
    for u_idx in range(1, num_units + 1):
        unit = Unit.objects.create(course=course, title=f"Unit {u_idx}", order=u_idx)
        for l_idx in range(1, lessons_per_unit + 1):
            Lesson.objects.create(unit=unit, title=f"Lesson {u_idx}.{l_idx}", order=l_idx)
    return course


def _enroll(student: User, course: Course) -> Enrollment:
    return Enrollment.objects.create(student=student, course=course, is_active=True)


# ---------------------------------------------------------------------------
# get_course_analytics
# ---------------------------------------------------------------------------


class TestGetCourseAnalytics:
    def test_empty_course_returns_zeros(self):
        teacher = _make_teacher()
        course = _make_course(teacher)

        result = AnalyticsService.get_course_analytics(course.pk)

        assert result.course_id == course.pk
        assert result.total_enrolled == 0
        assert result.average_completion_rate == 0.0
        assert result.average_score == 0.0
        assert result.average_time_per_lesson == 0.0

    def test_aggregates_enrolled_students(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=2)

        s1 = _make_user()
        s2 = _make_user()
        _enroll(s1, course)
        _enroll(s2, course)

        CourseProgress.objects.create(
            student=s1, course=course,
            completion_percentage=50.0, total_score=80.0,
            lessons_completed=1, total_lessons=2,
        )
        CourseProgress.objects.create(
            student=s2, course=course,
            completion_percentage=100.0, total_score=90.0,
            lessons_completed=2, total_lessons=2,
        )

        result = AnalyticsService.get_course_analytics(course.pk)

        assert result.total_enrolled == 2
        assert result.average_completion_rate == 75.0
        assert result.average_score == 85.0

    def test_average_time_per_lesson(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=2)

        s1 = _make_user()
        _enroll(s1, course)

        today = tz.localdate()
        DailyActivity.objects.create(
            student=s1, date=today,
            lessons_completed=2, xp_earned=100, time_spent_minutes=60,
        )

        result = AnalyticsService.get_course_analytics(course.pk)

        # 60 minutes / 2 lessons = 30 min per lesson
        assert result.average_time_per_lesson == 30.0

    def test_excludes_inactive_enrollments_from_total(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=1)

        s1 = _make_user()
        s2 = _make_user()
        _enroll(s1, course)
        Enrollment.objects.create(student=s2, course=course, is_active=False)

        result = AnalyticsService.get_course_analytics(course.pk)
        assert result.total_enrolled == 1


# ---------------------------------------------------------------------------
# get_student_list
# ---------------------------------------------------------------------------


class TestGetStudentList:
    def test_empty_course_returns_empty_list(self):
        teacher = _make_teacher()
        course = _make_course(teacher)

        result = AnalyticsService.get_student_list(course.pk)
        assert result == []

    def test_returns_student_progress_and_gamification(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=2)

        s1 = _make_user()
        _enroll(s1, course)

        CourseProgress.objects.create(
            student=s1, course=course,
            completion_percentage=75.0, total_score=88.0,
            lessons_completed=1, total_lessons=2,
        )
        GamificationProfile.objects.create(
            student=s1, total_xp=200, current_level=2,
            current_streak=5, last_activity_date=tz.localdate(),
        )

        result = AnalyticsService.get_student_list(course.pk)

        assert len(result) == 1
        entry = result[0]
        assert entry.student_id == s1.pk
        assert entry.progress_percentage == 75.0
        assert entry.score == 88.0
        assert entry.streak == 5
        assert entry.last_activity == tz.localdate()

    def test_defaults_for_student_without_progress(self):
        teacher = _make_teacher()
        course = _make_course(teacher)

        s1 = _make_user()
        _enroll(s1, course)

        result = AnalyticsService.get_student_list(course.pk)

        assert len(result) == 1
        entry = result[0]
        assert entry.progress_percentage == 0.0
        assert entry.score == 0.0
        assert entry.streak == 0
        assert entry.last_activity is None

    def test_excludes_inactive_enrollments(self):
        teacher = _make_teacher()
        course = _make_course(teacher)

        s1 = _make_user()
        s2 = _make_user()
        _enroll(s1, course)
        Enrollment.objects.create(student=s2, course=course, is_active=False)

        result = AnalyticsService.get_student_list(course.pk)
        assert len(result) == 1
        assert result[0].student_id == s1.pk

    def test_multiple_students_with_varying_progress(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=2)

        s1 = _make_user()
        s2 = _make_user()
        _enroll(s1, course)
        _enroll(s2, course)

        CourseProgress.objects.create(
            student=s1, course=course,
            completion_percentage=100.0, total_score=95.0,
            lessons_completed=2, total_lessons=2,
        )
        CourseProgress.objects.create(
            student=s2, course=course,
            completion_percentage=50.0, total_score=70.0,
            lessons_completed=1, total_lessons=2,
        )

        result = AnalyticsService.get_student_list(course.pk)

        assert len(result) == 2
        by_id = {e.student_id: e for e in result}
        assert by_id[s1.pk].progress_percentage == 100.0
        assert by_id[s1.pk].score == 95.0
        assert by_id[s2.pk].progress_percentage == 50.0
        assert by_id[s2.pk].score == 70.0


# ---------------------------------------------------------------------------
# get_student_detail
# ---------------------------------------------------------------------------


class TestGetStudentDetail:
    def test_returns_per_unit_per_lesson_detail(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=2, lessons_per_unit=2)

        student = _make_user()
        _enroll(student, course)

        # Complete one lesson
        lesson = Lesson.objects.filter(unit__course=course).first()
        LessonProgress.objects.create(
            student=student, lesson=lesson, is_completed=True, score=95.0,
        )
        CourseProgress.objects.create(
            student=student, course=course,
            completion_percentage=25.0, total_score=95.0,
            lessons_completed=1, total_lessons=4,
        )

        result = AnalyticsService.get_student_detail(course.pk, student.pk)

        assert result.student_id == student.pk
        assert result.completion_percentage == 25.0
        assert result.total_score == 95.0
        assert len(result.units) == 2
        assert len(result.units[0].lessons) == 2
        assert len(result.units[1].lessons) == 2

        # First lesson should be completed
        first_lesson = result.units[0].lessons[0]
        assert first_lesson.is_completed is True
        assert first_lesson.score == 95.0

    def test_returns_defaults_for_no_progress(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=1)

        student = _make_user()

        result = AnalyticsService.get_student_detail(course.pk, student.pk)

        assert result.completion_percentage == 0.0
        assert result.total_score == 0.0
        assert len(result.units) == 1
        assert result.units[0].lessons[0].is_completed is False
        assert result.units[0].lessons[0].score == 0.0


# ---------------------------------------------------------------------------
# get_performance_heatmap
# ---------------------------------------------------------------------------


class TestGetPerformanceHeatmap:
    def test_empty_course_returns_empty(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=1)

        result = AnalyticsService.get_performance_heatmap(course.pk)
        assert result == []

    def test_returns_accuracy_per_topic(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=1)
        lesson = Lesson.objects.filter(unit__course=course).first()

        ex1 = Exercise.objects.create(
            lesson=lesson, exercise_type="multiple_choice",
            question_text="Q1", order=1, config={}, topic="algebra",
        )
        ex2 = Exercise.objects.create(
            lesson=lesson, exercise_type="multiple_choice",
            question_text="Q2", order=2, config={}, topic="geometry",
        )

        student = _make_user()
        session = LessonSession.objects.create(
            student=student, lesson=lesson, total_exercises=2,
        )

        # algebra: 2 correct, 1 incorrect → 2/3
        AnswerRecord.objects.create(
            student=student, exercise=ex1, session=session,
            submitted_answer={}, is_correct=True, is_first_attempt=True,
        )
        AnswerRecord.objects.create(
            student=student, exercise=ex1, session=session,
            submitted_answer={}, is_correct=True, is_first_attempt=False,
        )
        AnswerRecord.objects.create(
            student=student, exercise=ex1, session=session,
            submitted_answer={}, is_correct=False, is_first_attempt=False,
        )

        # geometry: 1 correct, 1 incorrect → 1/2
        AnswerRecord.objects.create(
            student=student, exercise=ex2, session=session,
            submitted_answer={}, is_correct=True, is_first_attempt=True,
        )
        AnswerRecord.objects.create(
            student=student, exercise=ex2, session=session,
            submitted_answer={}, is_correct=False, is_first_attempt=False,
        )

        result = AnalyticsService.get_performance_heatmap(course.pk)

        assert len(result) == 2

        algebra = next(r for r in result if r.topic == "algebra")
        assert algebra.total_answers == 3
        assert algebra.correct_answers == 2
        assert algebra.accuracy == round(2 / 3, 4)

        geometry = next(r for r in result if r.topic == "geometry")
        assert geometry.total_answers == 2
        assert geometry.correct_answers == 1
        assert geometry.accuracy == 0.5

    def test_excludes_exercises_without_topic(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=1)
        lesson = Lesson.objects.filter(unit__course=course).first()

        # Exercise with no topic
        ex = Exercise.objects.create(
            lesson=lesson, exercise_type="multiple_choice",
            question_text="Q1", order=1, config={}, topic="",
        )

        student = _make_user()
        session = LessonSession.objects.create(
            student=student, lesson=lesson, total_exercises=1,
        )
        AnswerRecord.objects.create(
            student=student, exercise=ex, session=session,
            submitted_answer={}, is_correct=True, is_first_attempt=True,
        )

        result = AnalyticsService.get_performance_heatmap(course.pk)
        assert result == []

    def test_aggregates_across_multiple_students(self):
        teacher = _make_teacher()
        course = _make_course(teacher, num_units=1, lessons_per_unit=1)
        lesson = Lesson.objects.filter(unit__course=course).first()

        ex = Exercise.objects.create(
            lesson=lesson, exercise_type="multiple_choice",
            question_text="Q1", order=1, config={}, topic="algebra",
        )

        s1 = _make_user()
        s2 = _make_user()
        session1 = LessonSession.objects.create(student=s1, lesson=lesson, total_exercises=1)
        session2 = LessonSession.objects.create(student=s2, lesson=lesson, total_exercises=1)

        # s1: correct, s2: incorrect
        AnswerRecord.objects.create(
            student=s1, exercise=ex, session=session1,
            submitted_answer={}, is_correct=True, is_first_attempt=True,
        )
        AnswerRecord.objects.create(
            student=s2, exercise=ex, session=session2,
            submitted_answer={}, is_correct=False, is_first_attempt=True,
        )

        result = AnalyticsService.get_performance_heatmap(course.pk)

        assert len(result) == 1
        assert result[0].topic == "algebra"
        assert result[0].total_answers == 2
        assert result[0].correct_answers == 1
        assert result[0].accuracy == 0.5


# ---------------------------------------------------------------------------
# aggregate_analytics Celery task
# ---------------------------------------------------------------------------


class TestAggregateAnalyticsTask:
    def test_processes_published_courses(self):
        from apps.progress.tasks import aggregate_analytics

        teacher = _make_teacher()
        course1 = _make_course(teacher, num_units=1, lessons_per_unit=1)
        course2 = _make_course(teacher, num_units=1, lessons_per_unit=1)

        published_before = Course.objects.filter(
            status=Course.Status.PUBLISHED
        ).count()

        count = aggregate_analytics()

        assert count == published_before

    def test_skips_draft_courses(self):
        from apps.progress.tasks import aggregate_analytics

        teacher = _make_teacher()
        _make_course(teacher, num_units=1, lessons_per_unit=1)  # published
        Course.objects.create(
            title="Draft Course",
            description="A draft",
            teacher=teacher,
            status=Course.Status.DRAFT,
        )

        published_count = Course.objects.filter(
            status=Course.Status.PUBLISHED
        ).count()
        draft_count = Course.objects.filter(
            status=Course.Status.DRAFT
        ).count()

        count = aggregate_analytics()

        assert count == published_count
        assert draft_count >= 1  # at least our draft exists

    def test_returns_zero_when_no_courses(self):
        from unittest.mock import patch

        from apps.progress.tasks import aggregate_analytics

        # Patch Course.objects.filter to return empty queryset
        with patch(
            "apps.courses.models.Course.objects"
        ) as mock_manager:
            mock_manager.filter.return_value = []
            count = aggregate_analytics()

        assert count == 0

        assert count == 0

    def test_continues_on_individual_course_failure(self):
        from unittest.mock import patch

        from apps.progress.tasks import aggregate_analytics

        teacher = _make_teacher()
        course1 = _make_course(teacher, num_units=1, lessons_per_unit=1)
        course2 = _make_course(teacher, num_units=1, lessons_per_unit=1)

        published_count = Course.objects.filter(
            status=Course.Status.PUBLISHED
        ).count()

        original_get = AnalyticsService.get_course_analytics
        call_count = 0

        def fail_first(course_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated failure")
            return original_get(course_id)

        with patch.object(
            AnalyticsService, "get_course_analytics", side_effect=fail_first
        ):
            count = aggregate_analytics()

        # One failed, rest succeeded
        assert count == published_count - 1
