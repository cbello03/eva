"""CourseService — course management and enrollment business logic."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone as tz

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.courses.schemas import CourseCreateIn, CourseUpdateIn
from common.exceptions import (
    CourseNotPublishedError,
    DomainError,
    InsufficientRoleError,
    NotEnrolledError,
    PublishValidationError,
)
from common.sanitization import sanitize_html


class DuplicateEnrollmentError(DomainError):
    status_code = 409
    code = "duplicate_enrollment"

    def __init__(self, detail: str = "Already enrolled in this course"):
        super().__init__(detail)


class CourseNotFoundError(DomainError):
    status_code = 404
    code = "course_not_found"

    def __init__(self, detail: str = "Course not found"):
        super().__init__(detail)


class UnitNotFoundError(DomainError):
    status_code = 404
    code = "unit_not_found"

    def __init__(self, detail: str = "Unit not found"):
        super().__init__(detail)


class LessonNotFoundError(DomainError):
    status_code = 404
    code = "lesson_not_found"

    def __init__(self, detail: str = "Lesson not found"):
        super().__init__(detail)


def _check_course_owner(course: Course, user: User) -> None:
    """Raise if *user* is not the teacher who owns *course*."""
    if course.teacher_id != user.pk:
        raise InsufficientRoleError("You do not own this course")


class CourseService:
    """Handles course CRUD, publishing, ordering, and enrollment."""

    # ------------------------------------------------------------------
    # Course CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_course(teacher: User, data: CourseCreateIn) -> Course:
        """Create a new draft course for *teacher*."""
        return Course.objects.create(
            title=sanitize_html(data.title),
            description=sanitize_html(data.description),
            teacher=teacher,
            status=Course.Status.DRAFT,
        )

    @staticmethod
    def update_course(user: User, course_id: int, data: CourseUpdateIn) -> Course:
        """Update course fields. Only the owning teacher may update."""
        course = CourseService._get_course(course_id)
        _check_course_owner(course, user)

        if data.title is not None:
            course.title = sanitize_html(data.title)
        if data.description is not None:
            course.description = sanitize_html(data.description)
        course.save()
        return course

    @staticmethod
    def get_course(course_id: int) -> Course:
        """Return a course with prefetched units and lessons."""
        try:
            return (
                Course.objects.prefetch_related("units__lessons")
                .get(pk=course_id)
            )
        except Course.DoesNotExist:
            raise CourseNotFoundError()

    @staticmethod
    def publish_course(user: User, course_id: int) -> Course:
        """Publish a course after validation.

        Validation rules:
        - At least one unit must exist.
        - Every lesson must have at least one exercise.
        """
        course = CourseService._get_course(course_id)
        _check_course_owner(course, user)

        units = list(course.units.prefetch_related("lessons__exercises").all())
        if not units:
            raise PublishValidationError(
                "Course must have at least one unit to publish"
            )

        errors: list[str] = []
        for unit in units:
            for lesson in unit.lessons.all():
                if lesson.exercises.count() == 0:
                    errors.append(
                        f"Lesson '{lesson.title}' in unit '{unit.title}' "
                        f"has no exercises"
                    )

        if errors:
            raise PublishValidationError(
                "Some lessons have no exercises",
                errors=[{"field": "exercises", "message": e} for e in errors],
            )

        course.status = Course.Status.PUBLISHED
        course.published_at = tz.now()
        course.save(update_fields=["status", "published_at", "updated_at"])
        return course

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    @staticmethod
    def list_courses(user: User) -> QuerySet[Course]:
        """Return courses visible to *user*.

        Students see only published courses.
        Teachers see their own courses (draft + published).
        Admins see all courses.
        """
        if user.role == Role.ADMIN:
            return Course.objects.all().order_by("-created_at")
        if user.role == Role.TEACHER:
            return Course.objects.filter(teacher=user).order_by("-created_at")
        # Student — published only
        return Course.objects.filter(
            status=Course.Status.PUBLISHED
        ).order_by("-created_at")

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------

    @staticmethod
    def add_unit(user: User, course_id: int, title: str) -> Unit:
        """Add a unit to a course with the next sequential order."""
        course = CourseService._get_course(course_id)
        _check_course_owner(course, user)

        max_order = course.units.count()
        return Unit.objects.create(
            course=course,
            title=sanitize_html(title),
            order=max_order + 1,
        )

    @staticmethod
    def update_unit(user: User, unit_id: int, title: str | None = None) -> Unit:
        """Update a unit. Only the course owner may update."""
        unit = CourseService._get_unit(unit_id)
        _check_course_owner(unit.course, user)

        if title is not None:
            unit.title = sanitize_html(title)
        unit.save()
        return unit

    @staticmethod
    def reorder_units(user: User, course_id: int, ordered_ids: list[int]) -> None:
        """Reorder units within a course to match *ordered_ids* sequence."""
        course = CourseService._get_course(course_id)
        _check_course_owner(course, user)

        existing_ids = set(course.units.values_list("pk", flat=True))
        if set(ordered_ids) != existing_ids:
            raise DomainError("Provided IDs must match existing unit IDs exactly")

        with transaction.atomic():
            for new_order, unit_id in enumerate(ordered_ids, start=1):
                Unit.objects.filter(pk=unit_id, course=course).update(
                    order=new_order + 1000  # temp offset to avoid unique constraint
                )
            for new_order, unit_id in enumerate(ordered_ids, start=1):
                Unit.objects.filter(pk=unit_id, course=course).update(
                    order=new_order
                )

    # ------------------------------------------------------------------
    # Lessons
    # ------------------------------------------------------------------

    @staticmethod
    def add_lesson(user: User, unit_id: int, title: str) -> Lesson:
        """Add a lesson to a unit with the next sequential order."""
        unit = CourseService._get_unit(unit_id)
        _check_course_owner(unit.course, user)

        max_order = unit.lessons.count()
        return Lesson.objects.create(
            unit=unit,
            title=sanitize_html(title),
            order=max_order + 1,
        )

    @staticmethod
    def update_lesson(user: User, lesson_id: int, title: str | None = None) -> Lesson:
        """Update a lesson. Only the course owner may update."""
        lesson = CourseService._get_lesson(lesson_id)
        _check_course_owner(lesson.unit.course, user)

        if title is not None:
            lesson.title = sanitize_html(title)
        lesson.save()
        return lesson

    @staticmethod
    def reorder_lessons(user: User, unit_id: int, ordered_ids: list[int]) -> None:
        """Reorder lessons within a unit to match *ordered_ids* sequence."""
        unit = CourseService._get_unit(unit_id)
        _check_course_owner(unit.course, user)

        existing_ids = set(unit.lessons.values_list("pk", flat=True))
        if set(ordered_ids) != existing_ids:
            raise DomainError("Provided IDs must match existing lesson IDs exactly")

        with transaction.atomic():
            for new_order, lesson_id in enumerate(ordered_ids, start=1):
                Lesson.objects.filter(pk=lesson_id, unit=unit).update(
                    order=new_order + 1000
                )
            for new_order, lesson_id in enumerate(ordered_ids, start=1):
                Lesson.objects.filter(pk=lesson_id, unit=unit).update(
                    order=new_order
                )

    # ------------------------------------------------------------------
    # Enrollment
    # ------------------------------------------------------------------

    @staticmethod
    def enroll(student: User, course_id: int) -> Enrollment:
        """Enroll a student in a published course."""
        course = CourseService._get_course(course_id)

        if course.status != Course.Status.PUBLISHED:
            raise CourseNotPublishedError()

        # Check for existing enrollment (active or inactive)
        existing = Enrollment.objects.filter(
            student=student, course=course
        ).first()

        if existing is not None:
            if existing.is_active:
                raise DuplicateEnrollmentError()
            # Re-activate a previously deactivated enrollment
            existing.is_active = True
            existing.save(update_fields=["is_active", "updated_at"])
            return existing

        try:
            enrollment = Enrollment.objects.create(
                student=student, course=course
            )
        except IntegrityError:
            raise DuplicateEnrollmentError()

        # Initialize progress tracking (ProgressService not yet implemented,
        # will be wired in the progress app task)
        return enrollment

    @staticmethod
    def unenroll(student: User, course_id: int) -> None:
        """Deactivate enrollment. Preserves progress data."""
        try:
            enrollment = Enrollment.objects.get(
                student=student, course_id=course_id, is_active=True
            )
        except Enrollment.DoesNotExist:
            raise NotEnrolledError()

        enrollment.is_active = False
        enrollment.save(update_fields=["is_active", "updated_at"])

    @staticmethod
    def list_enrollments(student: User) -> list[dict]:
        """Return enrolled courses with progress percentage."""
        enrollments = (
            Enrollment.objects.filter(student=student, is_active=True)
            .select_related("course")
            .order_by("-enrolled_at")
        )
        results = []
        for enrollment in enrollments:
            results.append({
                "id": enrollment.pk,
                "course_id": enrollment.course_id,
                "course_title": enrollment.course.title,
                "is_active": enrollment.is_active,
                "enrolled_at": enrollment.enrolled_at,
                "progress_percentage": 0.0,  # Will be filled by ProgressService
            })
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_course(course_id: int) -> Course:
        try:
            return Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            raise CourseNotFoundError()

    @staticmethod
    def _get_unit(unit_id: int) -> Unit:
        try:
            return Unit.objects.select_related("course").get(pk=unit_id)
        except Unit.DoesNotExist:
            raise UnitNotFoundError()

    @staticmethod
    def _get_lesson(lesson_id: int) -> Lesson:
        try:
            return Lesson.objects.select_related("unit__course").get(pk=lesson_id)
        except Lesson.DoesNotExist:
            raise LessonNotFoundError()
