"""Collaboration app models — CollabGroup, CollabGroupMember, CollabSubmission."""

from django.db import models

from apps.accounts.models import User
from apps.exercises.models import Exercise
from common.models import TimestampedModel


class CollabGroup(TimestampedModel):
    """A collaboration group for a collaborative exercise."""

    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="collab_groups"
    )
    max_size = models.PositiveSmallIntegerField()
    workspace_state = models.JSONField(default=dict)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        db_table = "collaboration_collab_group"

    def __str__(self) -> str:
        return f"Group #{self.pk} for Exercise {self.exercise_id}"


class CollabGroupMember(TimestampedModel):
    """Tracks membership of a student in a collaboration group."""

    group = models.ForeignKey(
        CollabGroup, on_delete=models.CASCADE, related_name="members"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="collab_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_contribution_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "collaboration_collab_group_member"
        unique_together = [("group", "student")]

    def __str__(self) -> str:
        return f"{self.student.email} in Group #{self.group_id}"


class CollabSubmission(TimestampedModel):
    """Records a group's submitted work for a collaborative exercise."""

    group = models.ForeignKey(
        CollabGroup, on_delete=models.CASCADE, related_name="submissions"
    )
    submitted_answer = models.JSONField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "collaboration_collab_submission"

    def __str__(self) -> str:
        return f"Submission for Group #{self.group_id}"
