"""Tests for CourseService — CRUD, publishing, ordering, enrollment."""

from __future__ import annotations

import uuid

import pytest

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.courses.schemas import CourseCreateIn, CourseUpdateIn
from apps.courses.services import (
    CourseNotFoundError,
    CourseService,
    DuplicateEnrollmentError,
    LessonNotFoundError,
    UnitNotFoundError,
)
from apps.exercises.models import Exercise, ExerciseType
from common.exceptions import (
    CourseNotPublishedError,
    DomainError,
    InsufficientRoleError,
    NotEnrolledError,
    PublishValidationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_teacher(email: str = "teacher@example.com") -> User:
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"crs_teacher_{uid}",
        email=f"crs_teacher_{uid}@test.com",
        password="StrongPass1",
        display_name="Teacher",
        role=Role.TEACHER,
    )


def _make_student(email: str = "student@example.com") -> User:
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"crs_student_{uid}",
        email=f"crs_student_{uid}@test.com",
        password="StrongPass1",
        display_name="Student",
        role=Role.STUDENT,
    )


def _make_admin(email: str = "admin@example.com") -> User:
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"crs_admin_{uid}",
        email=f"crs_admin_{uid}@test.com",
        password="StrongPass1",
        display_name="Admin",
        role=Role.ADMIN,
    )


def _create_course(teacher: User, title: str = "Test Course") -> Course:
    return CourseService.create_course(
        teacher, CourseCreateIn(title=title, description="A test course")
    )


def _publish_ready_course(teacher: User) -> Course:
    """Create a course with one unit, one lesson, and one exercise — ready to publish."""
    course = _create_course(teacher)
    unit = CourseService.add_unit(teacher, course.pk, "Unit 1")
    lesson = CourseService.add_lesson(teacher, unit.pk, "Lesson 1")
    Exercise.objects.create(
        lesson=lesson,
        exercise_type=ExerciseType.MULTIPLE_CHOICE,
        question_text="What is 1+1?",
        order=1,
        config={"options": ["1", "2", "3"], "correct_index": 1},
    )
    return course


# ---------------------------------------------------------------------------
# Course CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateCourse:
    def test_creates_draft_course(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        assert course.title == "Test Course"
        assert course.status == Course.Status.DRAFT
        assert course.teacher == teacher

    def test_sanitizes_title_and_description(self):
        teacher = _make_teacher()
        course = CourseService.create_course(
            teacher,
            CourseCreateIn(
                title="<script>alert('xss')</script>Safe Title",
                description="<b>Bold</b> <script>bad</script>",
            ),
        )
        assert "<script>" not in course.title
        assert "<script>" not in course.description
        assert "<b>Bold</b>" in course.description


@pytest.mark.django_db
class TestUpdateCourse:
    def test_updates_title(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        updated = CourseService.update_course(
            teacher, course.pk, CourseUpdateIn(title="New Title")
        )
        assert updated.title == "New Title"

    def test_updates_description(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        updated = CourseService.update_course(
            teacher, course.pk, CourseUpdateIn(description="New desc")
        )
        assert updated.description == "New desc"

    def test_partial_update_preserves_other_fields(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        original_desc = course.description
        CourseService.update_course(
            teacher, course.pk, CourseUpdateIn(title="Changed")
        )
        course.refresh_from_db()
        assert course.title == "Changed"
        assert course.description == original_desc

    def test_non_owner_cannot_update(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        with pytest.raises(InsufficientRoleError):
            CourseService.update_course(
                other, course.pk, CourseUpdateIn(title="Hacked")
            )

    def test_update_nonexistent_course_raises(self):
        teacher = _make_teacher()
        with pytest.raises(CourseNotFoundError):
            CourseService.update_course(
                teacher, 99999, CourseUpdateIn(title="Nope")
            )


@pytest.mark.django_db
class TestGetCourse:
    def test_returns_course_with_hierarchy(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit 1")
        CourseService.add_lesson(teacher, unit.pk, "Lesson 1")

        fetched = CourseService.get_course(course.pk)
        assert fetched.pk == course.pk
        assert fetched.units.count() == 1
        assert fetched.units.first().lessons.count() == 1

    def test_nonexistent_course_raises(self):
        with pytest.raises(CourseNotFoundError):
            CourseService.get_course(99999)


# ---------------------------------------------------------------------------
# Publish validation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPublishCourse:
    def test_publish_succeeds_with_valid_course(self):
        teacher = _make_teacher()
        course = _publish_ready_course(teacher)
        published = CourseService.publish_course(teacher, course.pk)
        assert published.status == Course.Status.PUBLISHED
        assert published.published_at is not None

    def test_publish_fails_without_units(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        with pytest.raises(PublishValidationError, match="at least one unit"):
            CourseService.publish_course(teacher, course.pk)

    def test_publish_fails_when_lesson_has_no_exercises(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit 1")
        CourseService.add_lesson(teacher, unit.pk, "Empty Lesson")
        with pytest.raises(PublishValidationError, match="no exercises"):
            CourseService.publish_course(teacher, course.pk)

    def test_publish_fails_when_some_lessons_lack_exercises(self):
        """One lesson with exercises, another without — should fail."""
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit 1")
        lesson_ok = CourseService.add_lesson(teacher, unit.pk, "Good Lesson")
        CourseService.add_lesson(teacher, unit.pk, "Bad Lesson")
        Exercise.objects.create(
            lesson=lesson_ok,
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            question_text="Q?",
            order=1,
            config={"options": ["a", "b"], "correct_index": 0},
        )
        with pytest.raises(PublishValidationError):
            CourseService.publish_course(teacher, course.pk)

    def test_non_owner_cannot_publish(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _publish_ready_course(teacher)
        with pytest.raises(InsufficientRoleError):
            CourseService.publish_course(other, course.pk)

    def test_publish_nonexistent_course_raises(self):
        teacher = _make_teacher()
        with pytest.raises(CourseNotFoundError):
            CourseService.publish_course(teacher, 99999)


# ---------------------------------------------------------------------------
# Course listing by role
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestListCourses:
    def test_student_sees_only_published(self):
        teacher = _make_teacher()
        student = _make_student()
        _create_course(teacher, "Draft Course")
        pub = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, pub.pk)

        courses = list(CourseService.list_courses(student))
        # Filter to only courses created by this teacher to avoid cross-test leakage
        published = [c for c in courses if c.status == Course.Status.PUBLISHED and c.teacher_id == teacher.pk]
        assert len(published) == 1

    def test_teacher_sees_own_courses(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        _create_course(teacher, "My Course")
        _create_course(other, "Other Course")

        courses = list(CourseService.list_courses(teacher))
        assert len(courses) == 1
        assert courses[0].title == "My Course"

    def test_teacher_sees_draft_and_published(self):
        teacher = _make_teacher()
        _create_course(teacher, "Draft")
        pub = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, pub.pk)

        courses = list(CourseService.list_courses(teacher))
        statuses = {c.status for c in courses}
        assert Course.Status.DRAFT in statuses
        assert Course.Status.PUBLISHED in statuses

    def test_admin_sees_all_courses(self):
        teacher1 = _make_teacher()
        teacher2 = _make_teacher(email="t2@example.com")
        admin = _make_admin()
        c1 = _create_course(teacher1, "Course A")
        c2 = _create_course(teacher2, "Course B")

        courses = list(CourseService.list_courses(admin))
        course_ids = {c.pk for c in courses}
        assert c1.pk in course_ids
        assert c2.pk in course_ids


# ---------------------------------------------------------------------------
# Units — add, update, reorder
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUnits:
    def test_add_unit_assigns_sequential_order(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        u1 = CourseService.add_unit(teacher, course.pk, "Unit 1")
        u2 = CourseService.add_unit(teacher, course.pk, "Unit 2")
        u3 = CourseService.add_unit(teacher, course.pk, "Unit 3")
        assert u1.order == 1
        assert u2.order == 2
        assert u3.order == 3

    def test_add_unit_sanitizes_title(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "<script>x</script>Safe")
        assert "<script>" not in unit.title
        assert "Safe" in unit.title

    def test_add_unit_non_owner_raises(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        with pytest.raises(InsufficientRoleError):
            CourseService.add_unit(other, course.pk, "Nope")

    def test_update_unit_title(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Old Title")
        updated = CourseService.update_unit(teacher, unit.pk, title="New Title")
        assert updated.title == "New Title"

    def test_update_unit_non_owner_raises(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        with pytest.raises(InsufficientRoleError):
            CourseService.update_unit(other, unit.pk, title="Hacked")

    def test_update_nonexistent_unit_raises(self):
        teacher = _make_teacher()
        with pytest.raises(UnitNotFoundError):
            CourseService.update_unit(teacher, 99999, title="Nope")

    def test_reorder_units(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        u1 = CourseService.add_unit(teacher, course.pk, "Unit A")
        u2 = CourseService.add_unit(teacher, course.pk, "Unit B")
        u3 = CourseService.add_unit(teacher, course.pk, "Unit C")

        # Reverse the order
        CourseService.reorder_units(teacher, course.pk, [u3.pk, u2.pk, u1.pk])

        u1.refresh_from_db()
        u2.refresh_from_db()
        u3.refresh_from_db()
        assert u3.order == 1
        assert u2.order == 2
        assert u1.order == 3

    def test_reorder_units_contiguous_sequence(self):
        """After reorder, orders form 1..N with no gaps."""
        teacher = _make_teacher()
        course = _create_course(teacher)
        u1 = CourseService.add_unit(teacher, course.pk, "A")
        u2 = CourseService.add_unit(teacher, course.pk, "B")

        CourseService.reorder_units(teacher, course.pk, [u2.pk, u1.pk])
        orders = list(
            Unit.objects.filter(course=course).order_by("order").values_list("order", flat=True)
        )
        assert orders == [1, 2]

    def test_reorder_units_mismatched_ids_raises(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        CourseService.add_unit(teacher, course.pk, "Unit A")
        with pytest.raises(DomainError, match="must match"):
            CourseService.reorder_units(teacher, course.pk, [99999])

    def test_reorder_units_non_owner_raises(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        u1 = CourseService.add_unit(teacher, course.pk, "Unit")
        with pytest.raises(InsufficientRoleError):
            CourseService.reorder_units(other, course.pk, [u1.pk])


# ---------------------------------------------------------------------------
# Lessons — add, update, reorder
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLessons:
    def test_add_lesson_assigns_sequential_order(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit 1")
        l1 = CourseService.add_lesson(teacher, unit.pk, "Lesson 1")
        l2 = CourseService.add_lesson(teacher, unit.pk, "Lesson 2")
        assert l1.order == 1
        assert l2.order == 2

    def test_add_lesson_sanitizes_title(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        lesson = CourseService.add_lesson(teacher, unit.pk, "<img onerror=alert(1)>Lesson")
        assert "onerror" not in lesson.title

    def test_add_lesson_non_owner_raises(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        with pytest.raises(InsufficientRoleError):
            CourseService.add_lesson(other, unit.pk, "Nope")

    def test_update_lesson_title(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        lesson = CourseService.add_lesson(teacher, unit.pk, "Old")
        updated = CourseService.update_lesson(teacher, lesson.pk, title="New")
        assert updated.title == "New"

    def test_update_lesson_non_owner_raises(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        lesson = CourseService.add_lesson(teacher, unit.pk, "Lesson")
        with pytest.raises(InsufficientRoleError):
            CourseService.update_lesson(other, lesson.pk, title="Hacked")

    def test_update_nonexistent_lesson_raises(self):
        teacher = _make_teacher()
        with pytest.raises(LessonNotFoundError):
            CourseService.update_lesson(teacher, 99999, title="Nope")

    def test_reorder_lessons(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        l1 = CourseService.add_lesson(teacher, unit.pk, "A")
        l2 = CourseService.add_lesson(teacher, unit.pk, "B")
        l3 = CourseService.add_lesson(teacher, unit.pk, "C")

        CourseService.reorder_lessons(teacher, unit.pk, [l3.pk, l1.pk, l2.pk])

        l1.refresh_from_db()
        l2.refresh_from_db()
        l3.refresh_from_db()
        assert l3.order == 1
        assert l1.order == 2
        assert l2.order == 3

    def test_reorder_lessons_contiguous_sequence(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        l1 = CourseService.add_lesson(teacher, unit.pk, "A")
        l2 = CourseService.add_lesson(teacher, unit.pk, "B")

        CourseService.reorder_lessons(teacher, unit.pk, [l2.pk, l1.pk])
        orders = list(
            Lesson.objects.filter(unit=unit).order_by("order").values_list("order", flat=True)
        )
        assert orders == [1, 2]

    def test_reorder_lessons_mismatched_ids_raises(self):
        teacher = _make_teacher()
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        CourseService.add_lesson(teacher, unit.pk, "A")
        with pytest.raises(DomainError, match="must match"):
            CourseService.reorder_lessons(teacher, unit.pk, [99999])

    def test_reorder_lessons_non_owner_raises(self):
        teacher = _make_teacher()
        other = _make_teacher(email="other@example.com")
        course = _create_course(teacher)
        unit = CourseService.add_unit(teacher, course.pk, "Unit")
        l1 = CourseService.add_lesson(teacher, unit.pk, "A")
        with pytest.raises(InsufficientRoleError):
            CourseService.reorder_lessons(other, unit.pk, [l1.pk])


# ---------------------------------------------------------------------------
# Enrollment lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestEnrollment:
    def test_enroll_in_published_course(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)

        enrollment = CourseService.enroll(student, course.pk)
        assert enrollment.student == student
        assert enrollment.course == course
        assert enrollment.is_active is True

    def test_enroll_in_draft_course_raises(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _create_course(teacher)
        with pytest.raises(CourseNotPublishedError):
            CourseService.enroll(student, course.pk)

    def test_duplicate_enrollment_raises(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)
        CourseService.enroll(student, course.pk)

        with pytest.raises(DuplicateEnrollmentError):
            CourseService.enroll(student, course.pk)

    def test_unenroll_deactivates_enrollment(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)
        CourseService.enroll(student, course.pk)

        CourseService.unenroll(student, course.pk)
        enrollment = Enrollment.objects.get(student=student, course=course)
        assert enrollment.is_active is False

    def test_unenroll_preserves_record(self):
        """Unenrolling should not delete the enrollment row."""
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)
        CourseService.enroll(student, course.pk)
        CourseService.unenroll(student, course.pk)

        assert Enrollment.objects.filter(student=student, course=course).exists()

    def test_unenroll_when_not_enrolled_raises(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)

        with pytest.raises(NotEnrolledError):
            CourseService.unenroll(student, course.pk)

    def test_re_enroll_reactivates(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)

        CourseService.enroll(student, course.pk)
        CourseService.unenroll(student, course.pk)
        re_enrollment = CourseService.enroll(student, course.pk)

        assert re_enrollment.is_active is True
        # Should still be a single enrollment record
        assert Enrollment.objects.filter(student=student, course=course).count() == 1

    def test_enroll_nonexistent_course_raises(self):
        student = _make_student()
        with pytest.raises(CourseNotFoundError):
            CourseService.enroll(student, 99999)

    def test_list_enrollments_returns_active_only(self):
        teacher = _make_teacher()
        student = _make_student()
        c1 = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, c1.pk)
        CourseService.enroll(student, c1.pk)

        c2 = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, c2.pk)
        CourseService.enroll(student, c2.pk)
        CourseService.unenroll(student, c2.pk)

        enrollments = CourseService.list_enrollments(student)
        assert len(enrollments) == 1
        assert enrollments[0]["course_id"] == c1.pk

    def test_list_enrollments_includes_course_info(self):
        teacher = _make_teacher()
        student = _make_student()
        course = _publish_ready_course(teacher)
        CourseService.publish_course(teacher, course.pk)
        CourseService.enroll(student, course.pk)

        enrollments = CourseService.list_enrollments(student)
        assert len(enrollments) == 1
        item = enrollments[0]
        assert "course_title" in item
        assert "enrolled_at" in item
        assert "progress_percentage" in item
