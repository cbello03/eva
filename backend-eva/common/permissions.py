"""Role-based permission decorators for Django Ninja routes."""

from __future__ import annotations

import functools
from typing import Any, Callable

from common.exceptions import InsufficientRoleError


def require_role(*allowed_roles: str) -> Callable:
    """Decorator that restricts a Django Ninja endpoint to users with one of
    the given roles.

    Usage::

        @router.get("/admin-only")
        @require_role("admin")
        def admin_view(request):
            ...

    The decorator expects ``request.auth`` to be a user object with a
    ``role`` attribute (string).  If the user's role is not in
    *allowed_roles*, an ``InsufficientRoleError`` is raised which the
    global exception handler converts to a 403 response.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            user = getattr(request, "auth", None)
            if user is None:
                raise InsufficientRoleError("Authentication required")
            user_role = getattr(user, "role", None)
            if user_role not in allowed_roles:
                raise InsufficientRoleError(
                    f"Role '{user_role}' is not allowed. "
                    f"Required: {', '.join(allowed_roles)}"
                )
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
