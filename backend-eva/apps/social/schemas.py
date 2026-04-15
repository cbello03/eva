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


class ChatbotQuestionIn(Schema):
    """Payload for asking the course chatbot."""

    question: str
    mode: str = "brief"
    history: list[dict[str, str]] = []

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question is required")
        if len(v) > 2000:
            raise ValueError("Question must be at most 2000 characters")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"brief", "detailed"}:
            raise ValueError("mode must be 'brief' or 'detailed'")
        return v

    @field_validator("history")
    @classmethod
    def validate_history(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        if len(v) > 8:
            raise ValueError("history supports up to 8 recent turns")
        normalized: list[dict[str, str]] = []
        for item in v:
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip()
            if role not in {"user", "assistant"}:
                raise ValueError("history role must be 'user' or 'assistant'")
            if not content:
                raise ValueError("history content is required")
            if len(content) > 2000:
                raise ValueError("history content must be at most 2000 characters")
            normalized.append({"role": role, "content": content})
        return normalized


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------

class AuthorOut(Schema):
    """Lightweight author representation."""

    id: int
    display_name: str


class ReplyOut(Schema):
    """Forum reply representation in API responses."""

    id: int
    thread_id: int
    author: AuthorOut
    # Legacy flat fields kept for backward compatibility.
    author_id: int
    author_display_name: str
    body: str
    is_hidden: bool
    upvote_count: int
    has_upvoted: bool = False
    created_at: datetime


class ThreadOut(Schema):
    """Forum thread representation with replies."""

    id: int
    course_id: int
    author: AuthorOut
    # Legacy flat fields kept for backward compatibility.
    author_id: int
    author_display_name: str
    title: str
    body: str
    is_hidden: bool
    reply_count: int = 0
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
    author: AuthorOut
    # Legacy flat fields kept for backward compatibility.
    author_id: int
    author_display_name: str
    content: str
    sent_at: datetime


class ChatbotAnswerOut(Schema):
    """Course chatbot response."""

    course_id: int
    mode: str
    question: str
    answer: str
