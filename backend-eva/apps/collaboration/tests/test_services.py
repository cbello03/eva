"""Tests for CollaborationService — group assignment, submission, XP, inactive members."""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone as tz

from apps.accounts.models import Role, User
from apps.collaboration.models import CollabGroup, CollabGroupMember, CollabSubmission
from apps.collaboration.services import (
    CollaborationService,
    ExerciseNotCollaborativeError,
    ExerciseNotFoundError,
    GroupAlreadySubmittedError,
    GroupNotFoundError,
    NotGroupMemberError,
)
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import Exercise, ExerciseType
from apps.gamification.models import XPTransaction
from common.exceptions import NotEnrolledError


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def teacher(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"cs_teacher_{uid}",
        email=f"cs_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest.fixture
def student(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"cs_student_{uid}",
        email=f"cs_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def student2(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"cs_student2_{uid}",
        email=f"cs_student2_{uid}@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
    )


@pytest.fixture
def student3(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"cs_student3_{uid}",
        email=f"cs_student3_{uid}@test.com",
        password="Pass1234",
        display_name="Student Three",
        role=Role.STUDENT,
    )


@pytest.fixture
def course(teacher):
    return Course.objects.create(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def lesson(course):
    unit = Unit.objects.create(course=course, title="Unit 1", order=1)
    return Lesson.objects.create(unit=unit, title="Lesson 1", order=1)


@pytest.fixture
def collab_exercise(lesson):
    return Exercise.objects.create(
        lesson=lesson,
        exercise_type=ExerciseType.FREE_TEXT,
        question_text="Collaborative task",
        order=1,
        config={"model_answer": "answer", "rubric": "rubric"},
        is_collaborative=True,
        collab_group_size=3,
    )


@pytest.fixture
def non_collab_exercise(lesson):
    return Exercise.objects.create(
        lesson=lesson,
        exercise_type=ExerciseType.MULTIPLE_CHOICE,
        question_text="Non-collab",
        order=2,
        config={"options": ["A", "B"], "correct_index": 0},
        is_collaborative=False,
    )


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


@pytest.fixture
def enrollment2(student2, course):
    return Enrollment.objects.create(student=student2, course=course)


@pytest.fixture
def enrollment3(student3, course):
    return Enrollment.objects.create(student=student3, course=course)


# ------------------------------------------------------------------
# join_exercise — group assignment
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestJoinExercise:
    def test_creates_new_group_when_none_exist(self, student, collab_exercise, enrollment):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        assert group.pk is not None
        assert group.exercise == collab_exercise
        assert group.max_size == 3
        assert group.is_submitted is False
        assert CollabGroupMember.objects.filter(group=group, student=student).exists()

    def test_joins_existing_group_with_slots(
        self, student, student2, collab_exercise, enrollment, enrollment2
    ):
        group1 = CollaborationService.join_exercise(student, collab_exercise.pk)
        group2 = CollaborationService.join_exercise(student2, collab_exercise.pk)
        assert group1.pk == group2.pk
        assert CollabGroupMember.objects.filter(group=group1).count() == 2

    def test_creates_new_group_when_existing_full(
        self, student, student2, student3, collab_exercise, enrollment, enrollment2, enrollment3
    ):
        # collab_group_size=3, fill the first group
        collab_exercise.collab_group_size = 2
        collab_exercise.save()

        group1 = CollaborationService.join_exercise(student, collab_exercise.pk)
        group2 = CollaborationService.join_exercise(student2, collab_exercise.pk)
        assert group1.pk == group2.pk  # both in same group

        group3 = CollaborationService.join_exercise(student3, collab_exercise.pk)
        assert group3.pk != group1.pk  # new group created
        assert CollabGroupMember.objects.filter(group=group3, student=student3).exists()

    def test_returns_existing_group_if_already_joined(
        self, student, collab_exercise, enrollment
    ):
        group1 = CollaborationService.join_exercise(student, collab_exercise.pk)
        group2 = CollaborationService.join_exercise(student, collab_exercise.pk)
        assert group1.pk == group2.pk
        assert CollabGroupMember.objects.filter(group=group1, student=student).count() == 1

    def test_skips_submitted_groups(
        self, student, student2, collab_exercise, enrollment, enrollment2
    ):
        # Create a submitted group manually
        submitted_group = CollabGroup.objects.create(
            exercise=collab_exercise, max_size=3, is_submitted=True
        )
        CollabGroupMember.objects.create(group=submitted_group, student=student)

        # student2 should NOT be placed in the submitted group
        group = CollaborationService.join_exercise(student2, collab_exercise.pk)
        assert group.pk != submitted_group.pk

    def test_rejects_non_collaborative_exercise(
        self, student, non_collab_exercise, enrollment
    ):
        with pytest.raises(ExerciseNotCollaborativeError):
            CollaborationService.join_exercise(student, non_collab_exercise.pk)

    def test_rejects_unenrolled_student(self, student, collab_exercise):
        with pytest.raises(NotEnrolledError):
            CollaborationService.join_exercise(student, collab_exercise.pk)

    def test_rejects_nonexistent_exercise(self, student, enrollment):
        with pytest.raises(ExerciseNotFoundError):
            CollaborationService.join_exercise(student, 99999)

    def test_default_group_size_when_none(self, student, lesson, enrollment):
        exercise = Exercise.objects.create(
            lesson=lesson,
            exercise_type=ExerciseType.FREE_TEXT,
            question_text="Collab no size",
            order=3,
            config={"model_answer": "a", "rubric": "r"},
            is_collaborative=True,
            collab_group_size=None,
        )
        group = CollaborationService.join_exercise(student, exercise.pk)
        assert group.max_size == 2  # default


# ------------------------------------------------------------------
# submit_group_work — submission and XP distribution
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestSubmitGroupWork:
    def test_creates_submission(self, student, collab_exercise, enrollment):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        submission = CollaborationService.submit_group_work(
            student, group.pk, {"answer": "our solution"}
        )
        assert isinstance(submission, CollabSubmission)
        assert submission.submitted_answer == {"answer": "our solution"}
        assert submission.group == group

    def test_marks_group_as_submitted(self, student, collab_exercise, enrollment):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollaborationService.submit_group_work(student, group.pk, {"answer": "done"})
        group.refresh_from_db()
        assert group.is_submitted is True

    def test_awards_xp_to_all_members(
        self, student, student2, collab_exercise, enrollment, enrollment2
    ):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollaborationService.join_exercise(student2, collab_exercise.pk)

        CollaborationService.submit_group_work(student, group.pk, {"answer": "done"})

        txn1 = XPTransaction.objects.filter(student=student, source_type="collab")
        txn2 = XPTransaction.objects.filter(student=student2, source_type="collab")
        assert txn1.exists()
        assert txn2.exists()
        assert txn1.first().amount == txn2.first().amount == 10

    def test_rejects_double_submission(self, student, collab_exercise, enrollment):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollaborationService.submit_group_work(student, group.pk, {"answer": "first"})
        with pytest.raises(GroupAlreadySubmittedError):
            CollaborationService.submit_group_work(student, group.pk, {"answer": "second"})

    def test_rejects_non_member(self, student, student2, collab_exercise, enrollment, enrollment2):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        with pytest.raises(NotGroupMemberError):
            CollaborationService.submit_group_work(student2, group.pk, {"answer": "x"})

    def test_rejects_nonexistent_group(self, student, enrollment):
        with pytest.raises(GroupNotFoundError):
            CollaborationService.submit_group_work(student, 99999, {"answer": "x"})


# ------------------------------------------------------------------
# get_group_info
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestGetGroupInfo:
    def test_returns_group(self, student, collab_exercise, enrollment):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        result = CollaborationService.get_group_info(student, group.pk)
        assert result.pk == group.pk

    def test_rejects_non_member(self, student, student2, collab_exercise, enrollment, enrollment2):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        with pytest.raises(NotGroupMemberError):
            CollaborationService.get_group_info(student2, group.pk)

    def test_rejects_nonexistent_group(self, student, enrollment):
        with pytest.raises(GroupNotFoundError):
            CollaborationService.get_group_info(student, 99999)


# ------------------------------------------------------------------
# check_inactive_members
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCheckInactiveMembers:
    def test_detects_inactive_member_no_contribution(
        self, student, collab_exercise, enrollment
    ):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        # Backdate group creation to 49 hours ago
        CollabGroup.objects.filter(pk=group.pk).update(
            created_at=tz.now() - timedelta(hours=49)
        )
        inactive = CollaborationService.check_inactive_members(hours=48)
        student_ids = [m.student_id for m in inactive]
        assert student.pk in student_ids

    def test_detects_inactive_member_old_contribution(
        self, student, collab_exercise, enrollment
    ):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollabGroup.objects.filter(pk=group.pk).update(
            created_at=tz.now() - timedelta(hours=72)
        )
        CollabGroupMember.objects.filter(group=group, student=student).update(
            last_contribution_at=tz.now() - timedelta(hours=50)
        )
        inactive = CollaborationService.check_inactive_members(hours=48)
        student_ids = [m.student_id for m in inactive]
        assert student.pk in student_ids

    def test_excludes_recently_active_member(
        self, student, collab_exercise, enrollment
    ):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollabGroup.objects.filter(pk=group.pk).update(
            created_at=tz.now() - timedelta(hours=72)
        )
        CollabGroupMember.objects.filter(group=group, student=student).update(
            last_contribution_at=tz.now() - timedelta(hours=1)
        )
        inactive = CollaborationService.check_inactive_members(hours=48)
        student_ids = [m.student_id for m in inactive]
        assert student.pk not in student_ids

    def test_excludes_submitted_groups(
        self, student, collab_exercise, enrollment
    ):
        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollabGroup.objects.filter(pk=group.pk).update(
            created_at=tz.now() - timedelta(hours=72),
            is_submitted=True,
        )
        inactive = CollaborationService.check_inactive_members(hours=48)
        student_ids = [m.student_id for m in inactive]
        assert student.pk not in student_ids

    def test_excludes_recent_groups(
        self, student, collab_exercise, enrollment
    ):
        # Group created just now — not yet 48 hours old
        CollaborationService.join_exercise(student, collab_exercise.pk)
        inactive = CollaborationService.check_inactive_members(hours=48)
        assert len(inactive) == 0


# ------------------------------------------------------------------
# Celery task
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCheckInactiveCeleryTask:
    def test_task_returns_count(self, student, collab_exercise, enrollment):
        from apps.collaboration.tasks import check_inactive_collab_members

        group = CollaborationService.join_exercise(student, collab_exercise.pk)
        CollabGroup.objects.filter(pk=group.pk).update(
            created_at=tz.now() - timedelta(hours=49)
        )
        count = check_inactive_collab_members()
        assert count == 1

    def test_task_returns_zero_when_none_inactive(self, student, collab_exercise, enrollment):
        from apps.collaboration.tasks import check_inactive_collab_members

        CollaborationService.join_exercise(student, collab_exercise.pk)
        count = check_inactive_collab_members()
        assert count == 0
