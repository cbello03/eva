"""Courses API routes — course management, units, lessons, enrollment."""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Router

from apps.accounts.api import jwt_auth
from apps.accounts.models import Role
from apps.courses.schemas import (
    CourseCreateIn,
    CourseListOut,
    CourseOut,
    CourseUpdateIn,
    EnrollmentOut,
    LessonCreateIn,
    LessonOut,
    LessonUpdateIn,
    ReorderIn,
    UnitCreateIn,
    UnitOut,
    UnitUpdateIn,
)
from apps.courses.services import CourseService
from common.permissions import require_role

router = Router(tags=["courses"], auth=jwt_auth)


# ------------------------------------------------------------------
# Helper to build nested CourseOut from a Course instance
# ------------------------------------------------------------------

def _course_out(course) -> CourseOut:
    """Build a CourseOut with nested units and lessons."""
    units = []
    for unit in course.units.all().order_by("order"):
        lessons = [
            LessonOut(id=l.pk, title=l.title, order=l.order)
            for l in unit.lessons.all().order_by("order")
        ]
        units.append(UnitOut(
            id=unit.pk, title=unit.title, order=unit.order, lessons=lessons,
        ))
    return CourseOut(
        id=course.pk,
        title=course.title,
        description=course.description,
        teacher_id=course.teacher_id,
        status=course.status,
        published_at=course.published_at,
        created_at=course.created_at,
        updated_at=course.updated_at,
        units=units,
    )


# ------------------------------------------------------------------
# Course endpoints
# ------------------------------------------------------------------

@router.get("/courses", response=list[CourseListOut])
def list_courses(request: HttpRequest):
    """List courses visible to the authenticated user."""
    courses = CourseService.list_courses(request.auth)
    return [
        CourseListOut(
            id=c.pk,
            title=c.title,
            description=c.description,
            teacher_id=c.teacher_id,
            status=c.status,
            published_at=c.published_at,
            created_at=c.created_at,
        )
        for c in courses
    ]


@router.post("/courses", response={201: CourseOut})
@require_role(Role.TEACHER, Role.ADMIN)
def create_course(request: HttpRequest, payload: CourseCreateIn):
    """Create a new draft course (Teacher only)."""
    course = CourseService.create_course(request.auth, payload)
    return 201, _course_out(course)


@router.get("/courses/{course_id}", response=CourseOut)
def get_course(request: HttpRequest, course_id: int):
    """Get course detail with full unit/lesson hierarchy."""
    course = CourseService.get_course(course_id)
    return _course_out(course)


@router.patch("/courses/{course_id}", response=CourseOut)
@require_role(Role.TEACHER, Role.ADMIN)
def update_course(request: HttpRequest, course_id: int, payload: CourseUpdateIn):
    """Update course fields (Teacher+Owner only)."""
    course = CourseService.update_course(request.auth, course_id, payload)
    # Re-fetch with prefetched relations for the response
    course = CourseService.get_course(course_id)
    return _course_out(course)


@router.post("/courses/{course_id}/publish", response=CourseOut)
@require_role(Role.TEACHER, Role.ADMIN)
def publish_course(request: HttpRequest, course_id: int):
    """Publish a course after validation (Teacher+Owner only)."""
    course = CourseService.publish_course(request.auth, course_id)
    course = CourseService.get_course(course_id)
    return _course_out(course)


# ------------------------------------------------------------------
# Unit endpoints
# ------------------------------------------------------------------

@router.post("/courses/{course_id}/units", response={201: UnitOut})
@require_role(Role.TEACHER, Role.ADMIN)
def add_unit(request: HttpRequest, course_id: int, payload: UnitCreateIn):
    """Add a unit to a course (Teacher+Owner only)."""
    unit = CourseService.add_unit(request.auth, course_id, payload.title)
    return 201, UnitOut(id=unit.pk, title=unit.title, order=unit.order)


@router.patch("/units/{unit_id}", response=UnitOut)
@require_role(Role.TEACHER, Role.ADMIN)
def update_unit(request: HttpRequest, unit_id: int, payload: UnitUpdateIn):
    """Update a unit (Teacher+Owner only)."""
    unit = CourseService.update_unit(request.auth, unit_id, title=payload.title)
    return UnitOut(id=unit.pk, title=unit.title, order=unit.order)


@router.post("/courses/{course_id}/units/reorder", response={204: None})
@require_role(Role.TEACHER, Role.ADMIN)
def reorder_units(request: HttpRequest, course_id: int, payload: ReorderIn):
    """Reorder units within a course (Teacher+Owner only)."""
    CourseService.reorder_units(request.auth, course_id, payload.order)
    return 204, None


# ------------------------------------------------------------------
# Lesson endpoints
# ------------------------------------------------------------------

@router.post("/units/{unit_id}/lessons", response={201: LessonOut})
@require_role(Role.TEACHER, Role.ADMIN)
def add_lesson(request: HttpRequest, unit_id: int, payload: LessonCreateIn):
    """Add a lesson to a unit (Teacher+Owner only)."""
    lesson = CourseService.add_lesson(request.auth, unit_id, payload.title)
    return 201, LessonOut(id=lesson.pk, title=lesson.title, order=lesson.order)


@router.patch("/lessons/{lesson_id}", response=LessonOut)
@require_role(Role.TEACHER, Role.ADMIN)
def update_lesson(request: HttpRequest, lesson_id: int, payload: LessonUpdateIn):
    """Update a lesson (Teacher+Owner only)."""
    lesson = CourseService.update_lesson(
        request.auth, lesson_id, title=payload.title,
    )
    return LessonOut(id=lesson.pk, title=lesson.title, order=lesson.order)


@router.post("/units/{unit_id}/lessons/reorder", response={204: None})
@require_role(Role.TEACHER, Role.ADMIN)
def reorder_lessons(request: HttpRequest, unit_id: int, payload: ReorderIn):
    """Reorder lessons within a unit (Teacher+Owner only)."""
    CourseService.reorder_lessons(request.auth, unit_id, payload.order)
    return 204, None


# ------------------------------------------------------------------
# Enrollment endpoints
# ------------------------------------------------------------------

@router.post("/courses/{course_id}/enroll", response={201: EnrollmentOut})
@require_role(Role.STUDENT)
def enroll(request: HttpRequest, course_id: int):
    """Enroll in a published course (Student only)."""
    enrollment = CourseService.enroll(request.auth, course_id)
    return 201, EnrollmentOut(
        id=enrollment.pk,
        course_id=enrollment.course_id,
        course_title=enrollment.course.title,
        is_active=enrollment.is_active,
        enrolled_at=enrollment.enrolled_at,
        progress_percentage=0.0,
    )


@router.delete("/courses/{course_id}/enroll", response={204: None})
@require_role(Role.STUDENT)
def unenroll(request: HttpRequest, course_id: int):
    """Unenroll from a course (Student only). Preserves progress."""
    CourseService.unenroll(request.auth, course_id)
    return 204, None


@router.get("/enrollments", response=list[EnrollmentOut])
@require_role(Role.STUDENT)
def list_enrollments(request: HttpRequest):
    """List enrolled courses with progress (Student only)."""
    items = CourseService.list_enrollments(request.auth)
    return [EnrollmentOut(**item) for item in items]
