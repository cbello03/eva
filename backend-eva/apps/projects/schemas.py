"""Projects app Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime

from ninja import Schema
from pydantic import field_validator, model_validator


# ------------------------------------------------------------------
# File constraint constants
# ------------------------------------------------------------------

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILES_PER_SUBMISSION = 5


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class ProjectCreateIn(Schema):
    """Payload for creating a new project."""

    course_id: int
    title: str
    description: str
    rubric: list[dict]
    submission_deadline: datetime
    peer_review_enabled: bool = False
    peer_reviewers_count: int = 2

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > 200:
            raise ValueError("Title must be at most 200 characters")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Description is required")
        return v

    @field_validator("rubric")
    @classmethod
    def validate_rubric(cls, v: list[dict]) -> list[dict]:
        if len(v) < 1:
            raise ValueError("Rubric must have at least 1 criterion")
        for i, item in enumerate(v):
            if not isinstance(item, dict):
                raise ValueError(f"Rubric item {i} must be a dict")
            if "criterion" not in item or "max_score" not in item:
                raise ValueError(
                    f"Rubric item {i} must have 'criterion' and 'max_score' keys"
                )
            if not isinstance(item["criterion"], str) or not item["criterion"].strip():
                raise ValueError(f"Rubric item {i} 'criterion' must be a non-empty string")
            if not isinstance(item["max_score"], int) or item["max_score"] < 1:
                raise ValueError(f"Rubric item {i} 'max_score' must be a positive integer")
        return v

    @model_validator(mode="after")
    def validate_peer_reviewers_count(self) -> ProjectCreateIn:
        if self.peer_review_enabled and self.peer_reviewers_count < 2:
            raise ValueError(
                "peer_reviewers_count must be >= 2 when peer_review_enabled is True"
            )
        return self


class SubmissionCreateIn(Schema):
    """Payload for creating a project submission."""

    description: str = ""


class ReviewIn(Schema):
    """Payload for submitting a project review."""

    scores: dict[str, int | float]
    feedback: str = ""

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, v: dict[str, int | float]) -> dict[str, int | float]:
        for criterion, score in v.items():
            if score < 0:
                raise ValueError(
                    f"Score for '{criterion}' must be >= 0"
                )
        return v


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class ProjectOut(Schema):
    """Project representation in API responses."""

    id: int
    course_id: int
    teacher_id: int
    title: str
    description: str
    rubric: list[dict]
    submission_deadline: datetime
    peer_review_enabled: bool
    peer_reviewers_count: int
    created_at: datetime


class SubmissionFileOut(Schema):
    """Submission file representation in API responses."""

    id: int
    filename: str
    file_size: int


class SubmissionOut(Schema):
    """Project submission representation in API responses."""

    id: int
    project_id: int
    student_id: int
    description: str
    is_late: bool
    submitted_at: datetime
    files: list[SubmissionFileOut] = []


class ReviewOut(Schema):
    """Project review representation in API responses."""

    id: int
    submission_id: int
    reviewer_id: int
    review_type: str
    scores: dict
    feedback: str
    is_complete: bool
    created_at: datetime


class PeerReviewAssignmentOut(Schema):
    """Peer review assignment representation in API responses."""

    id: int
    submission_id: int
    reviewer_id: int
    is_completed: bool
