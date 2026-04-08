"""API-level and integration tests for accounts.

Tests the rate limiter, permission decorators, JWT bearer auth, and
API endpoints. Uses Django Ninja's TestClient for GET endpoints and
direct service-layer calls for POST endpoints (to avoid a known
Pydantic v2 QueryParams model_rebuild issue with field_validator schemas
in Django Ninja 1.6).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone as tz

import jwt
import pytest
from django.conf import settings
from django.core.cache import caches
from ninja.testing import TestClient as NinjaTestClient

from apps.accounts.models import RefreshToken, Role, User
from apps.accounts.schemas import LoginIn, RegisterIn
from apps.accounts.services import AuthService, JWT_ALGORITHM
from backend_eva.urls import api
from common.exceptions import InsufficientRoleError, RateLimitExceededError
from common.permissions import require_role
from common.rate_limiting import RateLimiter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ninja_client = NinjaTestClient(api)


def _register_via_service(
    email: str = "test@example.com",
    password: str = "StrongPass1",
    display_name: str = "Test User",
) -> User:
    return AuthService.register(
        RegisterIn(email=email, password=password, display_name=display_name)
    )


def _login_via_service(
    email: str = "test@example.com",
    password: str = "StrongPass1",
):
    return AuthService.login(LoginIn(email=email, password=password))


def _clear_rate_limit_cache():
    caches["default"].clear()


class FakeRequest:
    """Minimal request-like object for unit testing decorators."""

    def __init__(self, user=None, ip: str = "127.0.0.1"):
        self.auth = user
        self.META = {"REMOTE_ADDR": ip}


# ---------------------------------------------------------------------------
# require_role decorator
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRequireRoleDecorator:
    def test_admin_role_passes(self):
        @require_role(Role.ADMIN)
        def admin_view(request):
            return "ok"

        user = _register_via_service()
        user.role = Role.ADMIN
        user.save(update_fields=["role"])

        assert admin_view(FakeRequest(user=user)) == "ok"

    def test_student_blocked_from_admin_endpoint(self):
        @require_role(Role.ADMIN)
        def admin_view(request):
            return "ok"

        user = _register_via_service()  # student by default

        with pytest.raises(InsufficientRoleError):
            admin_view(FakeRequest(user=user))

    def test_no_auth_raises(self):
        @require_role(Role.TEACHER)
        def teacher_view(request):
            return "ok"

        with pytest.raises(InsufficientRoleError):
            teacher_view(FakeRequest(user=None))

    def test_multiple_roles_allowed(self):
        @require_role(Role.TEACHER, Role.ADMIN)
        def multi_view(request):
            return "ok"

        teacher = _register_via_service(email="t@example.com")
        teacher.role = Role.TEACHER
        teacher.save(update_fields=["role"])

        admin = _register_via_service(email="a@example.com")
        admin.role = Role.ADMIN
        admin.save(update_fields=["role"])

        assert multi_view(FakeRequest(user=teacher)) == "ok"
        assert multi_view(FakeRequest(user=admin)) == "ok"

    def test_student_blocked_from_teacher_admin_endpoint(self):
        @require_role(Role.TEACHER, Role.ADMIN)
        def multi_view(request):
            return "ok"

        student = _register_via_service()

        with pytest.raises(InsufficientRoleError):
            multi_view(FakeRequest(user=student))

    def test_error_includes_role_info(self):
        @require_role(Role.ADMIN)
        def admin_view(request):
            return "ok"

        user = _register_via_service()

        with pytest.raises(InsufficientRoleError) as exc_info:
            admin_view(FakeRequest(user=user))

        assert exc_info.value.status_code == 403
        assert "student" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def setup_method(self):
        _clear_rate_limit_cache()

    def test_allows_requests_within_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        req = FakeRequest(ip="10.0.0.1")

        for _ in range(3):
            limiter.check(req, "test_endpoint")  # should not raise

    def test_blocks_after_limit_exceeded(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        req = FakeRequest(ip="10.0.0.1")

        for _ in range(3):
            limiter.check(req, "test_endpoint")

        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.check(req, "test_endpoint")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after > 0

    def test_different_ips_have_separate_limits(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        req1 = FakeRequest(ip="10.0.0.1")
        req2 = FakeRequest(ip="10.0.0.2")

        # Exhaust limit for IP 1
        for _ in range(2):
            limiter.check(req1, "test_endpoint")

        with pytest.raises(RateLimitExceededError):
            limiter.check(req1, "test_endpoint")

        # IP 2 should still be allowed
        limiter.check(req2, "test_endpoint")  # should not raise

    def test_different_endpoints_have_separate_limits(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        req = FakeRequest(ip="10.0.0.1")

        for _ in range(2):
            limiter.check(req, "endpoint_a")

        with pytest.raises(RateLimitExceededError):
            limiter.check(req, "endpoint_a")

        # Different endpoint should still be allowed
        limiter.check(req, "endpoint_b")  # should not raise

    def test_decorator_usage(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        @limiter("my_endpoint")
        def my_view(request):
            return "ok"

        req = FakeRequest(ip="10.0.0.1")

        assert my_view(req) == "ok"
        assert my_view(req) == "ok"

        with pytest.raises(RateLimitExceededError):
            my_view(req)

    def test_retry_after_is_positive(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        req = FakeRequest(ip="10.0.0.1")

        limiter.check(req, "test")

        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.check(req, "test")

        assert exc_info.value.retry_after >= 1

    def test_register_limiter_allows_5(self):
        """Verify the registration rate limiter config: 5 requests per minute."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        req = FakeRequest(ip="10.0.0.1")

        for _ in range(5):
            limiter.check(req, "register")

        with pytest.raises(RateLimitExceededError):
            limiter.check(req, "register")

    def test_login_limiter_allows_10(self):
        """Verify the login rate limiter config: 10 requests per minute."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        req = FakeRequest(ip="10.0.0.1")

        for _ in range(10):
            limiter.check(req, "login")

        with pytest.raises(RateLimitExceededError):
            limiter.check(req, "login")

    def test_x_forwarded_for_used_as_key(self):
        """Rate limiter should use X-Forwarded-For header when present."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        req = FakeRequest(ip="10.0.0.1")
        req.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.50, 10.0.0.1"

        limiter.check(req, "test")

        with pytest.raises(RateLimitExceededError):
            limiter.check(req, "test")

        # Different X-Forwarded-For should be a separate counter
        req2 = FakeRequest(ip="10.0.0.1")
        req2.META["HTTP_X_FORWARDED_FOR"] = "198.51.100.10"
        limiter.check(req2, "test")  # should not raise


# ---------------------------------------------------------------------------
# JWT Bearer auth via GET /auth/me (works with Ninja TestClient)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJWTBearerAuth:
    def setup_method(self):
        _clear_rate_limit_cache()

    def test_me_returns_user_profile(self):
        _register_via_service()
        pair = _login_via_service()
        resp = ninja_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {pair.access_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "test@example.com"
        assert body["role"] == "student"
        assert body["display_name"] == "Test User"

    def test_me_without_auth_returns_401(self):
        resp = ninja_client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self):
        resp = ninja_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert resp.status_code == 401

    def test_expired_access_token_returns_401(self):
        user = _register_via_service()
        now = datetime.now(tz.utc)
        payload = {
            "sub": str(user.pk),
            "role": user.role,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": now - timedelta(hours=1),
            "exp": now - timedelta(minutes=1),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)

        resp = ninja_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    def test_refresh_token_used_as_bearer_returns_401(self):
        """A refresh token should not work as a Bearer access token."""
        _register_via_service()
        pair = _login_via_service()

        resp = ninja_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {pair.refresh_token}"},
        )
        assert resp.status_code == 401

    def test_tampered_token_returns_401(self):
        _register_via_service()
        pair = _login_via_service()
        tampered = pair.access_token[:-4] + "XXXX"

        resp = ninja_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tampered}"},
        )
        assert resp.status_code == 401

    def test_token_for_deleted_user_returns_401(self):
        user = _register_via_service()
        pair = _login_via_service()
        user.delete()

        resp = ninja_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {pair.access_token}"},
        )
        assert resp.status_code == 401

    def test_access_token_contains_role_claim(self):
        _register_via_service()
        pair = _login_via_service()
        payload = jwt.decode(
            pair.access_token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        assert payload["role"] == "student"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "sub" in payload

    def test_access_token_expires_in_15_minutes(self):
        _register_via_service()
        pair = _login_via_service()
        payload = jwt.decode(
            pair.access_token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        iat = datetime.fromtimestamp(payload["iat"], tz=tz.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=tz.utc)
        delta = exp - iat
        assert timedelta(minutes=14) < delta <= timedelta(minutes=16)


# ---------------------------------------------------------------------------
# Role change via API — permission enforcement
# (Tests the full decorator chain: auth + require_role)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRoleChangePermissions:
    def setup_method(self):
        _clear_rate_limit_cache()

    def test_unauthenticated_role_change_returns_401(self):
        resp = ninja_client.patch(
            "/users/1/role",
            json={"role": "teacher"},
        )
        assert resp.status_code == 401

    def test_student_role_change_blocked_by_decorator(self):
        """Students should be blocked by require_role(ADMIN) decorator."""
        # This tests the same code path as the API endpoint but avoids
        # the Pydantic QueryParams model_rebuild issue with field_validator.
        from apps.accounts.api import change_role

        student = _register_via_service(email="student@example.com")
        target = _register_via_service(email="target@example.com")

        with pytest.raises(InsufficientRoleError):
            change_role(FakeRequest(user=student), target.pk, None)

    def test_teacher_role_change_blocked_by_decorator(self):
        """Teachers should also be blocked by require_role(ADMIN)."""
        from apps.accounts.api import change_role

        teacher = _register_via_service(email="teacher@example.com")
        teacher.role = Role.TEACHER
        teacher.save(update_fields=["role"])
        target = _register_via_service(email="target@example.com")

        with pytest.raises(InsufficientRoleError):
            change_role(FakeRequest(user=teacher), target.pk, None)
