"""Courses app Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime

from ninja import Schema
from pydantic import field_validator


class CourseCreateIn(Schema):
    """Payload for creating a new course."""

    title: str
    description: str

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


class CourseUpdateIn(Schema):
    """Payload for updating a course (partial)."""

    title: str | None = None
    description: str | None = None


class UnitCreateIn(Schema):
    """Payload for creating a unit within a course."""

    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > 200:
            raise ValueError("Title must be at most 200 characters")
        return v


class UnitUpdateIn(Schema):
    """Payload for updating a unit."""

    title: str | None = None


class LessonCreateIn(Schema):
    """Payload for creating a lesson within a unit."""

    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > 200:
            raise ValueError("Title must be at most 200 characters")
        return v


class LessonUpdateIn(Schema):
    """Payload for updating a lesson."""

    title: str | None = None


class ReorderIn(Schema):
    """Payload for reordering units or lessons.

    ``order`` is a list of IDs in the desired order.
    """

    order: list[int]

    @field_validator("order")
    @classmethod
    def validate_order(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("Order list must not be empty")
        if len(v) != len(set(v)):
            raise ValueError("Order list must not contain duplicates")
        return v


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------

class LessonOut(Schema):
    """Lesson representation in API responses."""

    id: int
    title: str
    order: int


class UnitOut(Schema):
    """Unit representation with nested lessons."""

    id: int
    title: str
    order: int
    lessons: list[LessonOut] = []


class CourseOut(Schema):
    """Course representation with nested units/lessons."""

    id: int
    title: str
    description: str
    teacher_id: int
    status: str
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    units: list[UnitOut] = []


class CourseListOut(Schema):
    """Lightweight course representation for list endpoints."""

    id: int
    title: str
    description: str
    teacher_id: int
    status: str
    published_at: datetime | None = None
    created_at: datetime


class EnrollmentOut(Schema):
    """Enrollment representation with progress info."""

    id: int
    course_id: int
    course_title: str
    is_active: bool
    enrolled_at: datetime
    progress_percentage: float = 0.0
