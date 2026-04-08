"""AnalyticsService — teacher-facing analytics for courses and students."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from django.db.models import Avg, Count, F, Q, Sum

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import AnswerRecord, Exercise
from apps.progress.models import (
    CourseProgress,
    DailyActivity,
    LessonProgress,
)


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass
class CourseAnalytics:
    """Aggregate stats for a course (Requirement 16.1)."""

    course_id: int
    total_enrolled: int
    average_completion_rate: float
    average_score: float
    average_time_per_lesson: float  # minutes


@dataclass
class StudentListEntry:
    """Per-student row in the student list (Requirement 16.2)."""

    student_id: int
    email: str
    display_name: str
    progress_percentage: float
    score: float
    streak: int
    last_activity: datetime.date | None


@dataclass
class LessonDetail:
    lesson_id: int
    lesson_title: str
    is_completed: bool
    score: float


@dataclass
class UnitDetail:
    unit_id: int
    unit_title: str
    lessons: list[LessonDetail] = field(default_factory=list)


@dataclass
class StudentDetail:
    """Detailed progress for a single student in a course (Requirement 16.3)."""

    student_id: int
    email: str
    display_name: str
    completion_percentage: float
    total_score: float
    units: list[UnitDetail] = field(default_factory=list)


@dataclass
class TopicAccuracy:
    """Exercise accuracy for a single topic (Requirement 16.4)."""

    topic: str
    total_answers: int
    correct_answers: int
    accuracy: float  # 0.0–1.0


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AnalyticsService:
    """Teacher-facing analytics: course aggregates, student lists, detail, heatmap."""

    # ------------------------------------------------------------------
    # get_course_analytics  (Requirement 16.1)
    # ------------------------------------------------------------------

    @staticmethod
    def get_course_analytics(course_id: int) -> CourseAnalytics:
        """Return aggregate stats for a course.

        - total_enrolled: active enrollments
        - average_completion_rate: mean of CourseProgress.completion_percentage
        - average_score: mean of CourseProgress.total_score
        - average_time_per_lesson: mean daily time / mean lessons completed
        """
        course = Course.objects.get(pk=course_id)

        total_enrolled = Enrollment.objects.filter(
            course=course, is_active=True
        ).count()

        agg = CourseProgress.objects.filter(course=course).aggregate(
            avg_completion=Avg("completion_percentage"),
            avg_score=Avg("total_score"),
        )

        average_completion_rate = agg["avg_completion"] or 0.0
        average_score = agg["avg_score"] or 0.0

        # Average time per lesson: total time spent / total lessons completed
        # across all enrolled students.
        enrolled_student_ids = Enrollment.objects.filter(
            course=course, is_active=True
        ).values_list("student_id", flat=True)

        time_agg = DailyActivity.objects.filter(
            student_id__in=enrolled_student_ids,
        ).aggregate(
            total_time=Sum("time_spent_minutes"),
            total_lessons=Sum("lessons_completed"),
        )

        total_time = time_agg["total_time"] or 0
        total_lessons_done = time_agg["total_lessons"] or 0
        average_time_per_lesson = (
            total_time / total_lessons_done if total_lessons_done > 0 else 0.0
        )

        return CourseAnalytics(
            course_id=course.pk,
            total_enrolled=total_enrolled,
            average_completion_rate=round(average_completion_rate, 2),
            average_score=round(average_score, 2),
            average_time_per_lesson=round(average_time_per_lesson, 2),
        )

    # ------------------------------------------------------------------
    # get_student_list  (Requirement 16.2)
    # ------------------------------------------------------------------

    @staticmethod
    def get_student_list(course_id: int) -> list[StudentListEntry]:
        """Return per-student progress, score, streak, last activity for a course."""
        from apps.gamification.models import GamificationProfile

        course = Course.objects.get(pk=course_id)

        enrollments = (
            Enrollment.objects.filter(course=course, is_active=True)
            .select_related("student")
        )

        student_ids = [e.student_id for e in enrollments]

        # Bulk-fetch CourseProgress
        cp_map: dict[int, CourseProgress] = {
            cp.student_id: cp
            for cp in CourseProgress.objects.filter(
                course=course, student_id__in=student_ids
            )
        }

        # Bulk-fetch GamificationProfile
        gp_map: dict[int, GamificationProfile] = {
            gp.student_id: gp
            for gp in GamificationProfile.objects.filter(
                student_id__in=student_ids
            )
        }

        result: list[StudentListEntry] = []
        for enrollment in enrollments:
            student = enrollment.student
            cp = cp_map.get(student.pk)
            gp = gp_map.get(student.pk)

            result.append(
                StudentListEntry(
                    student_id=student.pk,
                    email=student.email,
                    display_name=student.display_name,
                    progress_percentage=cp.completion_percentage if cp else 0.0,
                    score=cp.total_score if cp else 0.0,
                    streak=gp.current_streak if gp else 0,
                    last_activity=gp.last_activity_date if gp else None,
                )
            )

        return result

    # ------------------------------------------------------------------
    # get_student_detail  (Requirement 16.3)
    # ------------------------------------------------------------------

    @staticmethod
    def get_student_detail(course_id: int, student_id: int) -> StudentDetail:
        """Return completion status and score per unit and lesson for a student."""
        course = Course.objects.get(pk=course_id)
        student = User.objects.get(pk=student_id)

        cp = CourseProgress.objects.filter(
            student=student, course=course
        ).first()

        units = (
            Unit.objects.filter(course=course)
            .prefetch_related("lessons")
            .order_by("order")
        )

        # Fetch all lesson progress for this student + course in one query
        lesson_ids = Lesson.objects.filter(
            unit__course=course
        ).values_list("pk", flat=True)

        lp_map: dict[int, LessonProgress] = {
            lp.lesson_id: lp
            for lp in LessonProgress.objects.filter(
                student=student, lesson_id__in=lesson_ids
            )
        }

        unit_data: list[UnitDetail] = []
        for unit in units:
            lesson_data: list[LessonDetail] = []
            for lesson in unit.lessons.all().order_by("order"):
                lp = lp_map.get(lesson.pk)
                lesson_data.append(
                    LessonDetail(
                        lesson_id=lesson.pk,
                        lesson_title=lesson.title,
                        is_completed=lp.is_completed if lp else False,
                        score=lp.score if lp else 0.0,
                    )
                )
            unit_data.append(
                UnitDetail(
                    unit_id=unit.pk,
                    unit_title=unit.title,
                    lessons=lesson_data,
                )
            )

        return StudentDetail(
            student_id=student.pk,
            email=student.email,
            display_name=student.display_name,
            completion_percentage=cp.completion_percentage if cp else 0.0,
            total_score=cp.total_score if cp else 0.0,
            units=unit_data,
        )

    # ------------------------------------------------------------------
    # get_performance_heatmap  (Requirement 16.4)
    # ------------------------------------------------------------------

    @staticmethod
    def get_performance_heatmap(course_id: int) -> list[TopicAccuracy]:
        """Return exercise accuracy rates across topics for a course.

        Groups all AnswerRecord rows for exercises in this course by topic,
        computing correct/total and accuracy ratio.
        """
        course = Course.objects.get(pk=course_id)

        # All exercises in this course that have a topic tag
        exercise_ids = Exercise.objects.filter(
            lesson__unit__course=course,
        ).exclude(topic="").values_list("pk", flat=True)

        # Aggregate answer records grouped by exercise topic
        topic_stats = (
            AnswerRecord.objects.filter(exercise_id__in=exercise_ids)
            .values(topic=F("exercise__topic"))
            .annotate(
                total_answers=Count("id"),
                correct_answers=Count("id", filter=Q(is_correct=True)),
            )
            .order_by("topic")
        )

        return [
            TopicAccuracy(
                topic=row["topic"],
                total_answers=row["total_answers"],
                correct_answers=row["correct_answers"],
                accuracy=(
                    round(row["correct_answers"] / row["total_answers"], 4)
                    if row["total_answers"] > 0
                    else 0.0
                ),
            )
            for row in topic_stats
        ]
