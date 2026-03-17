"""Cursor / offset pagination utilities for Django Ninja."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from ninja import Schema


class PaginationParams(Schema):
    """Query parameters accepted by paginated endpoints."""

    offset: int = 0
    limit: int = 20


class PaginatedResponse(Schema):
    """Envelope returned by paginated endpoints."""

    count: int
    next_offset: int | None = None
    results: list[Any]


def paginate(
    queryset: QuerySet,
    params: PaginationParams,
) -> PaginatedResponse:
    """Apply offset-based pagination to *queryset*.

    Returns a ``PaginatedResponse`` with the total count, the items for
    the current page, and the offset for the next page (``None`` when
    there are no more results).
    """
    total = queryset.count()
    limit = max(1, min(params.limit, 100))  # clamp between 1 and 100
    offset = max(0, params.offset)

    items = list(queryset[offset : offset + limit])

    next_offset = offset + limit if offset + limit < total else None

    return PaginatedResponse(
        count=total,
        next_offset=next_offset,
        results=items,
    )
