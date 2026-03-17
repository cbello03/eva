"""Redis-based rate limiter for Django Ninja endpoints."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable

from django.core.cache import caches

from common.exceptions import RateLimitExceededError


class RateLimiter:
    """Sliding-window rate limiter backed by the default Django Redis cache.

    Parameters
    ----------
    max_requests:
        Maximum number of requests allowed within *window_seconds*.
    window_seconds:
        Length of the sliding window in seconds.
    key_func:
        Optional callable ``(request) -> str`` that returns the cache key
        component identifying the caller.  Defaults to client IP.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60,
        key_func: Callable | None = None,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_func = key_func or self._default_key

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_key(request: Any) -> str:
        """Extract client IP from the request."""
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _cache_key(self, request: Any, endpoint: str) -> str:
        caller = self.key_func(request)
        return f"rate_limit:{endpoint}:{caller}"

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def check(self, request: Any, endpoint: str) -> None:
        """Raise ``RateLimitExceededError`` if the caller has exceeded the
        limit for *endpoint*.
        """
        cache = caches["default"]
        key = self._cache_key(request, endpoint)
        now = time.time()
        window_start = now - self.window_seconds

        # Use a sorted-set-like approach with a list of timestamps.
        timestamps: list[float] = cache.get(key) or []

        # Prune entries outside the window.
        timestamps = [ts for ts in timestamps if ts > window_start]

        if len(timestamps) >= self.max_requests:
            oldest = min(timestamps)
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            raise RateLimitExceededError(
                detail="Too many requests",
                retry_after=max(retry_after, 1),
            )

        timestamps.append(now)
        cache.set(key, timestamps, timeout=self.window_seconds + 1)

    # ------------------------------------------------------------------
    # Decorator
    # ------------------------------------------------------------------

    def __call__(self, endpoint: str | None = None) -> Callable:
        """Use as a decorator on a Django Ninja route function.

        Usage::

            login_limiter = RateLimiter(max_requests=10, window_seconds=60)

            @router.post("/login")
            @login_limiter("login")
            def login(request, payload: LoginIn):
                ...
        """

        def decorator(func: Callable) -> Callable:
            ep = endpoint or func.__qualname__

            @functools.wraps(func)
            def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                self.check(request, ep)
                return func(request, *args, **kwargs)

            return wrapper

        return decorator
