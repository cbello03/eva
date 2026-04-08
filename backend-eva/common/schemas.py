"""Shared Pydantic schemas for API responses."""

from ninja import Schema


class FieldError(Schema):
    """Describes a validation error on a single field."""

    field: str
    message: str


class ErrorResponse(Schema):
    """Standard error response body returned by the global exception handler."""

    detail: str
    code: str
    errors: list[FieldError] = []
