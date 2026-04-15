"""ProgressService — student progress tracking, dashboard, heatmap, mastery."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import Avg
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.progress.models import (
    CourseProgress,
    DailyActivity,
    LessonProgress,
    TopicMastery,
)


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass
class DashboardData:
    total_xp: int
    current_level: int
    current_streak: int
    courses_enrolled: int
    courses_completed: int


@dataclass
class LessonProgressData:
    lesson_id: int
    lesson_title: str
    is_completed: bool
    score: float


@dataclass
class UnitProgressData:
    unit_id: int
    unit_title: str
    lessons: list[LessonProgressData] = field(default_factory=list)


@dataclass
class CourseProgressData:
    course_id: int
    course_title: str
    completion_percentage: float
    total_score: float
    lessons_completed: int
    total_lessons: int
    units: list[UnitProgressData] = field(default_factory=list)


@dataclass
class ActivityDay:
    date: datetime.date
    lessons_completed: int
    xp_earned: int
    time_spent_minutes: int


@dataclass
class MasteryScore:
    topic: str
    correct_count: int
    total_count: int
    mastery_score: float
    last_reviewed: datetime.datetime | None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ProgressService:
    """Handles student progress tracking, dashboards, and analytics."""

    # ------------------------------------------------------------------
    # Initialize progress on enrollment
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def initialize_course_progress(student: User, course_id: int) -> CourseProgress:
        """Create CourseProgress + LessonProgress for every lesson in the course.

        Called when a student enrolls. Idempotent — skips if already exists.
        """
        course = Course.objects.get(pk=course_id)

        lessons = Lesson.objects.filter(unit__course=course).select_related("unit")
        total_lessons = lessons.count()

        course_progress, created = CourseProgress.objects.get_or_create(
            student=student,
            course=course,
            defaults={"total_lessons": total_lessons},
        )

        if not created:
            # Already initialised — update total_lessons in case course changed
            course_progress.total_lessons = total_lessons
            course_progress.save(update_fields=["total_lessons", "updated_at"])

        # Bulk-create LessonProgress rows (skip existing via ignore_conflicts)
        lesson_progress_objs = [
            LessonProgress(student=student, lesson=lesson)
            for lesson in lessons
        ]
        LessonProgress.objects.bulk_create(
            lesson_progress_objs, ignore_conflicts=True
        )

        return course_progress

    # ------------------------------------------------------------------
    # Update lesson progress
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def update_lesson_progress(
        student: User, lesson_id: int, score: float
    ) -> LessonProgress:
        """Mark a lesson completed, update score, recalculate course completion."""
        lesson = Lesson.objects.select_related("unit__course").get(pk=lesson_id)
        course = lesson.unit.course

        lp, _ = LessonProgress.objects.get_or_create(
            student=student, lesson=lesson
        )

        lp.is_completed = True
        lp.score = score
        lp.completed_at = tz.now()
        lp.save(update_fields=["is_completed", "score", "completed_at", "updated_at"])

        # Recalculate CourseProgress
        cp, _ = CourseProgress.objects.get_or_create(
            student=student, course=course
        )

        all_lessons = Lesson.objects.filter(unit__course=course)
        total = all_lessons.count()
        completed = LessonProgress.objects.filter(
            student=student,
            lesson__in=all_lessons,
            is_completed=True,
        ).count()

        agg = LessonProgress.objects.filter(
            student=student,
            lesson__in=all_lessons,
            is_completed=True,
        ).aggregate(avg_score=Avg("score"))

        cp.total_lessons = total
        cp.lessons_completed = completed
        cp.completion_percentage = (completed / total * 100.0) if total > 0 else 0.0
        cp.total_score = agg["avg_score"] or 0.0
        cp.save(
            update_fields=[
                "total_lessons",
                "lessons_completed",
                "completion_percentage",
                "total_score",
                "updated_at",
            ]
        )

        return lp

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @staticmethod
    def get_dashboard(student: User) -> DashboardData:
        """Return overall stats: XP, level, streak, enrolled/completed counts."""
        from apps.gamification.models import GamificationProfile

        try:
            profile = GamificationProfile.objects.get(student=student)
            total_xp = profile.total_xp
            current_level = profile.current_level
            current_streak = profile.current_streak
        except GamificationProfile.DoesNotExist:
            total_xp = 0
            current_level = 1
            current_streak = 0

        courses_enrolled = Enrollment.objects.filter(
            student=student, is_active=True
        ).count()

        courses_completed = CourseProgress.objects.filter(
            student=student, completion_percentage__gte=100.0
        ).count()

        return DashboardData(
            total_xp=total_xp,
            current_level=current_level,
            current_streak=current_streak,
            courses_enrolled=courses_enrolled,
            courses_completed=courses_completed,
        )

    # ------------------------------------------------------------------
    # Course progress detail
    # ------------------------------------------------------------------

    @staticmethod
    def get_course_progress(student: User, course_id: int) -> CourseProgressData:
        """Return per-unit, per-lesson completion and score for a course."""
        course = Course.objects.get(pk=course_id)

        cp = CourseProgress.objects.filter(student=student, course=course).first()
        completion_percentage = cp.completion_percentage if cp else 0.0
        total_score = cp.total_score if cp else 0.0
        lessons_completed = cp.lessons_completed if cp else 0
        total_lessons = cp.total_lessons if cp else 0

        units = (
            Unit.objects.filter(course=course)
            .prefetch_related("lessons")
            .order_by("order")
        )

        # Fetch all lesson progress for this student + course in one query
        lesson_ids = Lesson.objects.filter(unit__course=course).values_list(
            "pk", flat=True
        )
        lp_map: dict[int, LessonProgress] = {
            lp.lesson_id: lp
            for lp in LessonProgress.objects.filter(
                student=student, lesson_id__in=lesson_ids
            )
        }

        unit_data: list[UnitProgressData] = []
        for unit in units:
            lesson_data: list[LessonProgressData] = []
            for lesson in unit.lessons.all().order_by("order"):
                lp = lp_map.get(lesson.pk)
                lesson_data.append(
                    LessonProgressData(
                        lesson_id=lesson.pk,
                        lesson_title=lesson.title,
                        is_completed=lp.is_completed if lp else False,
                        score=lp.score if lp else 0.0,
                    )
                )
            unit_data.append(
                UnitProgressData(
                    unit_id=unit.pk,
                    unit_title=unit.title,
                    lessons=lesson_data,
                )
            )

        return CourseProgressData(
            course_id=course.pk,
            course_title=course.title,
            completion_percentage=completion_percentage,
            total_score=total_score,
            lessons_completed=lessons_completed,
            total_lessons=total_lessons,
            units=unit_data,
        )

    # ------------------------------------------------------------------
    # Activity heatmap
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def record_daily_activity(
        student: User,
        *,
        lessons_completed: int = 0,
        xp_earned: int = 0,
        time_spent_minutes: int = 0,
    ) -> DailyActivity:
        """Upsert daily activity totals for the student.

        This method aggregates activity for the current local date.
        """
        today = tz.localdate()
        activity, _ = DailyActivity.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                "lessons_completed": 0,
                "xp_earned": 0,
                "time_spent_minutes": 0,
            },
        )
        activity.lessons_completed += max(0, lessons_completed)
        activity.xp_earned += max(0, xp_earned)
        activity.time_spent_minutes += max(0, time_spent_minutes)
        activity.save(
            update_fields=[
                "lessons_completed",
                "xp_earned",
                "time_spent_minutes",
                "updated_at",
            ]
        )
        return activity

    @staticmethod
    def get_activity_heatmap(
        student: User, days: int = 90
    ) -> list[ActivityDay]:
        """Return last *days* of DailyActivity, filling missing days with zeros."""
        today = tz.localdate()
        start_date = today - datetime.timedelta(days=days - 1)

        # Fetch existing records in range
        records = DailyActivity.objects.filter(
            student=student,
            date__gte=start_date,
            date__lte=today,
        )
        record_map: dict[datetime.date, DailyActivity] = {
            r.date: r for r in records
        }

        result: list[ActivityDay] = []
        current = start_date
        while current <= today:
            rec = record_map.get(current)
            if rec:
                result.append(
                    ActivityDay(
                        date=current,
                        lessons_completed=rec.lessons_completed,
                        xp_earned=rec.xp_earned,
                        time_spent_minutes=rec.time_spent_minutes,
                    )
                )
            else:
                result.append(
                    ActivityDay(
                        date=current,
                        lessons_completed=0,
                        xp_earned=0,
                        time_spent_minutes=0,
                    )
                )
            current += datetime.timedelta(days=1)

        return result

    # ------------------------------------------------------------------
    # Mastery scores
    # ------------------------------------------------------------------

    @staticmethod
    def get_mastery_scores(student: User) -> list[MasteryScore]:
        """Return TopicMastery data per topic for the student."""
        records = TopicMastery.objects.filter(student=student).order_by("topic")

        return [
            MasteryScore(
                topic=tm.topic,
                correct_count=tm.correct_count,
                total_count=tm.total_count,
                mastery_score=tm.mastery_score,
                last_reviewed=tm.last_reviewed,
            )
            for tm in records
        ]
