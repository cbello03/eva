"""Accounts API routes — authentication, profile, and role management."""

from __future__ import annotations

import jwt
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from ninja import Router
from ninja.security import HttpBearer

from apps.accounts.models import Role, User
from apps.accounts.schemas import (
    LoginIn,
    RegisterIn,
    RoleChangeIn,
    TokenOut,
    UserOut,
)
from apps.accounts.services import AuthService, JWT_ALGORITHM, REFRESH_TOKEN_LIFETIME
from common.exceptions import InvalidCredentialsError
from common.permissions import require_role
from common.rate_limiting import RateLimiter


# ---------------------------------------------------------------------------
# Django Ninja Bearer auth scheme
# ---------------------------------------------------------------------------

class JWTBearer(HttpBearer):
    """Validate a Bearer access token and return the authenticated User."""

    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["sub", "role", "exp", "type"]},
            )
        except jwt.PyJWTError:
            return None

        if payload.get("type") != "access":
            return None

        try:
            return User.objects.get(pk=int(payload["sub"]))
        except (User.DoesNotExist, ValueError):
            return None


jwt_auth = JWTBearer()

router = Router(tags=["auth"])

# ---------------------------------------------------------------------------
# Rate limiters
# ---------------------------------------------------------------------------
_register_limiter = RateLimiter(max_requests=5, window_seconds=60)
_login_limiter = RateLimiter(max_requests=10, window_seconds=60)

# ---------------------------------------------------------------------------
# Cookie settings
# ---------------------------------------------------------------------------
_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = int(REFRESH_TOKEN_LIFETIME.total_seconds())


def _set_refresh_cookie(response: HttpResponse, token: str) -> HttpResponse:
    """Set the refresh token as an httpOnly secure cookie."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Lax",
        path="/api/v1/auth/",
    )
    return response


def _clear_refresh_cookie(response: HttpResponse) -> HttpResponse:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        path="/api/v1/auth/",
        samesite="Lax",
    )
    return response


# ---------------------------------------------------------------------------
# Public endpoints (no auth, rate limited)
# ---------------------------------------------------------------------------

@router.post("/auth/register", response={201: UserOut}, auth=None)
@_register_limiter("register")
def register(request: HttpRequest, payload: RegisterIn):
    """Register a new student account."""
    user = AuthService.register(payload)
    return 201, UserOut(
        id=user.pk,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        timezone=user.timezone,
    )


@router.post("/auth/login", response=TokenOut, auth=None)
@_login_limiter("login")
def login(request: HttpRequest, payload: LoginIn):
    """Authenticate and return an access token. Sets refresh token as cookie."""
    pair = AuthService.login(payload)
    body = TokenOut(access_token=pair.access_token)
    response = router.api.create_response(request, body.dict(), status=200)
    return _set_refresh_cookie(response, pair.refresh_token)


# ---------------------------------------------------------------------------
# Cookie-based endpoint (no Bearer, reads cookie)
# ---------------------------------------------------------------------------

@router.post("/auth/refresh", response=TokenOut, auth=None)
def refresh(request: HttpRequest):
    """Rotate tokens using the refresh token cookie."""
    refresh_token = request.COOKIES.get(_REFRESH_COOKIE, "")
    if not refresh_token:
        raise InvalidCredentialsError("No refresh token provided")

    pair = AuthService.refresh_tokens(refresh_token)
    body = TokenOut(access_token=pair.access_token)
    response = router.api.create_response(request, body.dict(), status=200)
    return _set_refresh_cookie(response, pair.refresh_token)


# ---------------------------------------------------------------------------
# Authenticated endpoints (Bearer JWT)
# ---------------------------------------------------------------------------

@router.post("/auth/logout", response={204: None}, auth=jwt_auth)
def logout(request: HttpRequest):
    """Logout — revoke refresh token and clear cookie."""
    refresh_token = request.COOKIES.get(_REFRESH_COOKIE, "")
    if refresh_token:
        AuthService.logout(refresh_token)

    response = router.api.create_response(request, None, status=204)
    return _clear_refresh_cookie(response)


@router.get("/auth/me", response=UserOut, auth=jwt_auth)
def me(request: HttpRequest):
    """Return the current authenticated user's profile."""
    user = request.auth  # type: ignore[union-attr]
    return UserOut(
        id=user.pk,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        timezone=user.timezone,
    )


@router.patch("/users/{user_id}/role", response=UserOut, auth=jwt_auth)
@require_role(Role.ADMIN)
def change_role(request: HttpRequest, user_id: int, payload: RoleChangeIn):
    """Change a user's role (Admin only)."""
    updated = AuthService.change_role(user_id, payload.role)
    return UserOut(
        id=updated.pk,
        email=updated.email,
        display_name=updated.display_name,
        role=updated.role,
        timezone=updated.timezone,
    )
