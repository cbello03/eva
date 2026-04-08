"""Progress and analytics API routes — student progress + teacher analytics."""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Router

from apps.accounts.api import jwt_auth
from apps.accounts.models import Role
from apps.courses.models import Course, Enrollment
from apps.progress.analytics import AnalyticsService
from apps.progress.schemas import (
    ActivityDayOut,
    CourseAnalyticsOut,
    CourseProgressOut,
    DashboardOut,
    LessonProgressOut,
    MasteryScoreOut,
    StudentDetailOut,
    StudentListEntryOut,
    TeacherLessonDetailOut,
    TeacherUnitDetailOut,
    TopicAccuracyOut,
    UnitProgressOut,
)
from apps.progress.services import ProgressService
from common.exceptions import InsufficientRoleError, NotEnrolledError
from common.permissions import require_role

router = Router(tags=["progress"], auth=jwt_auth)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _verify_course_owner(user, course_id: int) -> Course:
    """Verify the user is the teacher who owns the course. Returns the course."""
    course = Course.objects.get(pk=course_id)
    if course.teacher_id != user.pk:
        raise InsufficientRoleError("You do not own this course")
    return course


def _verify_enrolled(user, course_id: int) -> None:
    """Verify the student is actively enrolled in the course."""
    if not Enrollment.objects.filter(
        student=user, course_id=course_id, is_active=True
    ).exists():
        raise NotEnrolledError()


# ---------------------------------------------------------------------------
# Student progress endpoints
# ---------------------------------------------------------------------------


@router.get("/progress/dashboard", response=DashboardOut)
@require_role(Role.STUDENT)
def get_dashboard(request: HttpRequest):
    """Return overall student stats: XP, level, streak, enrolled/completed."""
    data = ProgressService.get_dashboard(request.auth)
    return DashboardOut(
        total_xp=data.total_xp,
        current_level=data.current_level,
        current_streak=data.current_streak,
        courses_enrolled=data.courses_enrolled,
        courses_completed=data.courses_completed,
    )


@router.get("/progress/courses/{course_id}", response=CourseProgressOut)
@require_role(Role.STUDENT)
def get_course_progress(request: HttpRequest, course_id: int):
    """Return per-course progress detail (requires enrollment)."""
    _verify_enrolled(request.auth, course_id)
    data = ProgressService.get_course_progress(request.auth, course_id)
    return CourseProgressOut(
        course_id=data.course_id,
        course_title=data.course_title,
        completion_percentage=data.completion_percentage,
        total_score=data.total_score,
        lessons_completed=data.lessons_completed,
        total_lessons=data.total_lessons,
        units=[
            UnitProgressOut(
                unit_id=u.unit_id,
                unit_title=u.unit_title,
                lessons=[
                    LessonProgressOut(
                        lesson_id=lp.lesson_id,
                        lesson_title=lp.lesson_title,
                        is_completed=lp.is_completed,
                        score=lp.score,
                    )
                    for lp in u.lessons
                ],
            )
            for u in data.units
        ],
    )


@router.get("/progress/activity", response=list[ActivityDayOut])
@require_role(Role.STUDENT)
def get_activity_heatmap(request: HttpRequest):
    """Return 90-day activity heatmap data."""
    days = ProgressService.get_activity_heatmap(request.auth, days=90)
    return [
        ActivityDayOut(
            date=d.date,
            lessons_completed=d.lessons_completed,
            xp_earned=d.xp_earned,
            time_spent_minutes=d.time_spent_minutes,
        )
        for d in days
    ]


@router.get("/progress/mastery", response=list[MasteryScoreOut])
@require_role(Role.STUDENT)
def get_mastery_scores(request: HttpRequest):
    """Return topic mastery scores for the student."""
    scores = ProgressService.get_mastery_scores(request.auth)
    return [
        MasteryScoreOut(
            topic=s.topic,
            correct_count=s.correct_count,
            total_count=s.total_count,
            mastery_score=s.mastery_score,
            last_reviewed=s.last_reviewed,
        )
        for s in scores
    ]


# ---------------------------------------------------------------------------
# Teacher analytics endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/teacher/courses/{course_id}/analytics",
    response=CourseAnalyticsOut,
)
@require_role(Role.TEACHER, Role.ADMIN)
def get_course_analytics(request: HttpRequest, course_id: int):
    """Return aggregate course stats (Teacher+Owner only)."""
    _verify_course_owner(request.auth, course_id)
    data = AnalyticsService.get_course_analytics(course_id)
    return CourseAnalyticsOut(
        course_id=data.course_id,
        total_enrolled=data.total_enrolled,
        average_completion_rate=data.average_completion_rate,
        average_score=data.average_score,
        average_time_per_lesson=data.average_time_per_lesson,
    )


@router.get(
    "/teacher/courses/{course_id}/students",
    response=list[StudentListEntryOut],
)
@require_role(Role.TEACHER, Role.ADMIN)
def get_student_list(request: HttpRequest, course_id: int):
    """Return student list with progress for a course (Teacher+Owner only)."""
    _verify_course_owner(request.auth, course_id)
    entries = AnalyticsService.get_student_list(course_id)
    return [
        StudentListEntryOut(
            student_id=e.student_id,
            email=e.email,
            display_name=e.display_name,
            progress_percentage=e.progress_percentage,
            score=e.score,
            streak=e.streak,
            last_activity=e.last_activity,
        )
        for e in entries
    ]


@router.get(
    "/teacher/courses/{course_id}/students/{student_id}",
    response=StudentDetailOut,
)
@require_role(Role.TEACHER, Role.ADMIN)
def get_student_detail(request: HttpRequest, course_id: int, student_id: int):
    """Return detailed student progress for a course (Teacher+Owner only)."""
    _verify_course_owner(request.auth, course_id)
    data = AnalyticsService.get_student_detail(course_id, student_id)
    return StudentDetailOut(
        student_id=data.student_id,
        email=data.email,
        display_name=data.display_name,
        completion_percentage=data.completion_percentage,
        total_score=data.total_score,
        units=[
            TeacherUnitDetailOut(
                unit_id=u.unit_id,
                unit_title=u.unit_title,
                lessons=[
                    TeacherLessonDetailOut(
                        lesson_id=lp.lesson_id,
                        lesson_title=lp.lesson_title,
                        is_completed=lp.is_completed,
                        score=lp.score,
                    )
                    for lp in u.lessons
                ],
            )
            for u in data.units
        ],
    )


@router.get(
    "/teacher/courses/{course_id}/heatmap",
    response=list[TopicAccuracyOut],
)
@require_role(Role.TEACHER, Role.ADMIN)
def get_performance_heatmap(request: HttpRequest, course_id: int):
    """Return exercise accuracy heatmap by topic (Teacher+Owner only)."""
    _verify_course_owner(request.auth, course_id)
    topics = AnalyticsService.get_performance_heatmap(course_id)
    return [
        TopicAccuracyOut(
            topic=t.topic,
            total_answers=t.total_answers,
            correct_answers=t.correct_answers,
            accuracy=t.accuracy,
        )
        for t in topics
    ]
