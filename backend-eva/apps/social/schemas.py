"""Social app Pydantic schemas for request/response validation."""

from datetime import datetime

from ninja import Schema
from pydantic import field_validator


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------

class ThreadCreateIn(Schema):
    """Payload for creating a new forum thread."""

    title: str
    body: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > 200:
            raise ValueError("Title must be at most 200 characters")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Body is required")
        return v


class ReplyCreateIn(Schema):
    """Payload for replying to a forum thread."""

    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Body is required")
        return v


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------

class ReplyOut(Schema):
    """Forum reply representation in API responses."""

    id: int
    thread_id: int
    author_id: int
    author_display_name: str
    body: str
    is_hidden: bool
    upvote_count: int
    created_at: datetime


class ThreadOut(Schema):
    """Forum thread representation with replies."""

    id: int
    course_id: int
    author_id: int
    author_display_name: str
    title: str
    body: str
    is_hidden: bool
    last_activity_at: datetime
    created_at: datetime
    replies: list[ReplyOut] = []


class ThreadListOut(Schema):
    """Paginated thread list response."""

    count: int
    next_offset: int | None = None
    results: list[ThreadOut]


class ChatMessageOut(Schema):
    """Chat message representation in API/WebSocket responses."""

    id: int
    course_id: int
    author_id: int
    author_display_name: str
    content: str
    sent_at: datetime
