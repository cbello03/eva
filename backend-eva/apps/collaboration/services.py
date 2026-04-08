"""CollaborationService — group exercises and shared workspaces."""

from __future__ import annotations

from django.db import models, transaction
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.collaboration.models import CollabGroup, CollabGroupMember, CollabSubmission
from apps.courses.models import Enrollment
from apps.exercises.models import Exercise
from common.exceptions import DomainError, NotEnrolledError


class ExerciseNotCollaborativeError(DomainError):
    status_code = 400
    code = "exercise_not_collaborative"

    def __init__(self, detail: str = "This exercise is not collaborative"):
        super().__init__(detail)


class GroupNotFoundError(DomainError):
    status_code = 404
    code = "group_not_found"

    def __init__(self, detail: str = "Collaboration group not found"):
        super().__init__(detail)


class NotGroupMemberError(DomainError):
    status_code = 403
    code = "not_group_member"

    def __init__(self, detail: str = "You are not a member of this group"):
        super().__init__(detail)


class GroupAlreadySubmittedError(DomainError):
    status_code = 400
    code = "group_already_submitted"

    def __init__(self, detail: str = "This group has already submitted"):
        super().__init__(detail)


class ExerciseNotFoundError(DomainError):
    status_code = 404
    code = "exercise_not_found"

    def __init__(self, detail: str = "Exercise not found"):
        super().__init__(detail)


def _check_enrollment(user: User, exercise: Exercise) -> None:
    """Raise if user is not enrolled in the course containing the exercise."""
    course = exercise.lesson.unit.course
    if not Enrollment.objects.filter(
        student=user, course=course, is_active=True
    ).exists():
        raise NotEnrolledError()


class CollaborationService:
    """Handles group exercises, membership, submissions, and inactivity checks."""

    @staticmethod
    @transaction.atomic
    def join_exercise(student: User, exercise_id: int) -> CollabGroup:
        """Join a collaborative exercise.

        Finds a group with available slots or creates a new one.
        Returns the group the student was added to.
        """
        try:
            exercise = Exercise.objects.select_related(
                "lesson__unit__course"
            ).get(pk=exercise_id)
        except Exercise.DoesNotExist:
            raise ExerciseNotFoundError()

        if not exercise.is_collaborative:
            raise ExerciseNotCollaborativeError()

        _check_enrollment(student, exercise)

        max_size = exercise.collab_group_size or 2

        # Check if student is already in a group for this exercise
        existing = CollabGroupMember.objects.filter(
            student=student, group__exercise=exercise
        ).select_related("group").first()
        if existing:
            return existing.group

        # Find a group with available slots
        group = (
            CollabGroup.objects.filter(
                exercise=exercise,
                is_submitted=False,
            )
            .annotate(member_count=models.Count("members"))
            .filter(member_count__lt=max_size)
            .order_by("created_at")
            .first()
        )

        if group is None:
            group = CollabGroup.objects.create(
                exercise=exercise,
                max_size=max_size,
            )

        CollabGroupMember.objects.create(
            group=group,
            student=student,
        )
        return group

    @staticmethod
    @transaction.atomic
    def submit_group_work(
        student: User, group_id: int, submitted_answer: dict
    ) -> CollabSubmission:
        """Submit group work and award equal XP to all members."""
        group = CollaborationService._get_group(group_id)
        CollaborationService._check_membership(student, group)

        if group.is_submitted:
            raise GroupAlreadySubmittedError()

        submission = CollabSubmission.objects.create(
            group=group,
            submitted_answer=submitted_answer,
        )

        group.is_submitted = True
        group.save(update_fields=["is_submitted", "updated_at"])

        # Award XP to all group members
        from apps.gamification.services import GamificationService

        members = CollabGroupMember.objects.filter(group=group).select_related("student")
        for member in members:
            GamificationService.award_xp(
                student=member.student,
                source_type="collab",
                source_id=group.exercise_id,
                amount=10,
            )

        return submission

    @staticmethod
    def get_group_info(student: User, group_id: int) -> CollabGroup:
        """Return group with members and workspace state."""
        group = CollaborationService._get_group(group_id)
        CollaborationService._check_membership(student, group)
        return group

    @staticmethod
    def check_inactive_members(hours: int = 48) -> list[CollabGroupMember]:
        """Find group members with no contribution within *hours* of group creation.

        Returns list of inactive members for notification.
        """
        threshold = tz.now() - tz.timedelta(hours=hours)
        inactive = CollabGroupMember.objects.filter(
            group__is_submitted=False,
            group__created_at__lte=threshold,
        ).filter(
            models.Q(last_contribution_at__isnull=True)
            | models.Q(last_contribution_at__lte=threshold)
        ).select_related("student", "group__exercise__lesson__unit__course")
        return list(inactive)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_group(group_id: int) -> CollabGroup:
        try:
            return CollabGroup.objects.select_related("exercise").get(pk=group_id)
        except CollabGroup.DoesNotExist:
            raise GroupNotFoundError()

    @staticmethod
    def _check_membership(student: User, group: CollabGroup) -> None:
        if not CollabGroupMember.objects.filter(
            group=group, student=student
        ).exists():
            raise NotGroupMemberError()
