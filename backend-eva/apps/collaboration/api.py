"""Collaboration API routes — group exercises and shared workspaces."""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Router

from apps.accounts.api import jwt_auth
from apps.collaboration.schemas import (
    CollabGroupMemberOut,
    CollabGroupOut,
    CollabSubmissionOut,
    GroupSubmitIn,
)
from apps.collaboration.services import CollaborationService

router = Router(tags=["collaboration"], auth=jwt_auth)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _group_out(group) -> CollabGroupOut:
    """Build a CollabGroupOut from a CollabGroup instance."""
    members = [
        CollabGroupMemberOut(
            id=m.pk,
            student_id=m.student_id,
            student_display_name=m.student.display_name,
            joined_at=m.joined_at,
            last_contribution_at=m.last_contribution_at,
        )
        for m in group.members.select_related("student").all()
    ]
    return CollabGroupOut(
        id=group.pk,
        exercise_id=group.exercise_id,
        max_size=group.max_size,
        workspace_state=group.workspace_state,
        is_submitted=group.is_submitted,
        members=members,
        created_at=group.created_at,
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/exercises/{exercise_id}/collab/join", response={201: CollabGroupOut})
def join_collab_exercise(request: HttpRequest, exercise_id: int):
    """Join a collaborative exercise (find or create a group)."""
    group = CollaborationService.join_exercise(request.auth, exercise_id)
    return 201, _group_out(group)


@router.post("/collab/groups/{group_id}/submit", response={201: CollabSubmissionOut})
def submit_group_work(
    request: HttpRequest, group_id: int, payload: GroupSubmitIn
):
    """Submit group work for a collaborative exercise."""
    submission = CollaborationService.submit_group_work(
        request.auth, group_id, payload.submitted_answer
    )
    return 201, CollabSubmissionOut(
        id=submission.pk,
        group_id=submission.group_id,
        submitted_answer=submission.submitted_answer,
        submitted_at=submission.submitted_at,
    )


@router.get("/collab/groups/{group_id}", response=CollabGroupOut)
def get_group_info(request: HttpRequest, group_id: int):
    """Get group info and workspace state."""
    group = CollaborationService.get_group_info(request.auth, group_id)
    return _group_out(group)
