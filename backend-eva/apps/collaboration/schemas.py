"""Collaboration app Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any

from ninja import Schema


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------

class GroupSubmitIn(Schema):
    """Payload for submitting group work."""

    submitted_answer: dict[str, Any]


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------

class CollabGroupMemberOut(Schema):
    """Collaboration group member representation."""

    id: int
    student_id: int
    student_display_name: str
    joined_at: datetime
    last_contribution_at: datetime | None = None


class CollabGroupOut(Schema):
    """Collaboration group representation."""

    id: int
    exercise_id: int
    max_size: int
    workspace_state: dict[str, Any]
    is_submitted: bool
    members: list[CollabGroupMemberOut] = []
    created_at: datetime


class CollabSubmissionOut(Schema):
    """Collaboration submission representation."""

    id: int
    group_id: int
    submitted_answer: dict[str, Any]
    submitted_at: datetime
