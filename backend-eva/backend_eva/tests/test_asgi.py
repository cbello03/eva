"""Tests for ASGI routing and JWTAuthMiddleware."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
import pytest_asyncio
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import Role, User
from apps.accounts.services import JWT_ALGORITHM
from backend_eva.asgi import JWTAuthMiddleware, _get_user_from_token


def _make_jwt(user: User, *, token_type: str = "access", expired: bool = False) -> str:
    delta = timedelta(minutes=-1) if expired else timedelta(minutes=15)
    payload = {
        "sub": str(user.pk),
        "role": user.role,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + delta,
    }
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


@pytest_asyncio.fixture
async def user():
    uid = uuid.uuid4().hex[:8]
    return await database_sync_to_async(User.objects.create_user)(
        username=f"asgi_user_{uid}",
        email=f"asgi_user_{uid}@test.com",
        password="Pass1234",
        display_name="ASGI User",
        role=Role.STUDENT,
    )


# ------------------------------------------------------------------
# _get_user_from_token helper
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGetUserFromToken:
    async def test_valid_token_returns_user(self, user):
        token = _make_jwt(user)
        result = await _get_user_from_token(token)
        assert result.pk == user.pk

    async def test_expired_token_returns_anonymous(self, user):
        token = _make_jwt(user, expired=True)
        result = await _get_user_from_token(token)
        assert isinstance(result, AnonymousUser)

    async def test_refresh_type_returns_anonymous(self, user):
        token = _make_jwt(user, token_type="refresh")
        result = await _get_user_from_token(token)
        assert isinstance(result, AnonymousUser)

    async def test_invalid_token_returns_anonymous(self):
        result = await _get_user_from_token("not.a.valid.jwt")
        assert isinstance(result, AnonymousUser)

    async def test_nonexistent_user_returns_anonymous(self):
        payload = {
            "sub": "99999",
            "role": "student",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
        result = await _get_user_from_token(token)
        assert isinstance(result, AnonymousUser)


# ------------------------------------------------------------------
# JWTAuthMiddleware integration
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestJWTAuthMiddleware:
    async def test_middleware_sets_user_on_scope(self, user):
        """Middleware should populate scope['user'] with the authenticated user."""
        token = _make_jwt(user)
        captured_scope = {}

        async def mock_app(scope, receive, send):
            captured_scope.update(scope)

        middleware = JWTAuthMiddleware(mock_app)
        scope = {
            "type": "websocket",
            "query_string": f"token={token}".encode(),
        }
        await middleware(scope, None, None)
        assert captured_scope["user"].pk == user.pk

    async def test_middleware_sets_anonymous_without_token(self):
        """No token in query string should result in AnonymousUser."""
        captured_scope = {}

        async def mock_app(scope, receive, send):
            captured_scope.update(scope)

        middleware = JWTAuthMiddleware(mock_app)
        scope = {"type": "websocket", "query_string": b""}
        await middleware(scope, None, None)
        assert isinstance(captured_scope["user"], AnonymousUser)

    async def test_middleware_sets_anonymous_with_bad_token(self):
        """Invalid token should result in AnonymousUser."""
        captured_scope = {}

        async def mock_app(scope, receive, send):
            captured_scope.update(scope)

        middleware = JWTAuthMiddleware(mock_app)
        scope = {
            "type": "websocket",
            "query_string": b"token=bad.jwt.token",
        }
        await middleware(scope, None, None)
        assert isinstance(captured_scope["user"], AnonymousUser)


# ------------------------------------------------------------------
# ASGI application routing sanity check
# ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestASGIRouting:
    async def test_chat_route_exists(self, user):
        """ws/chat/<course_id>/ should be routable (connection may fail auth/enrollment)."""
        from backend_eva.asgi import application

        token = _make_jwt(user)
        comm = WebsocketCommunicator(
            application, f"/ws/chat/1/?token={token}"
        )
        # We just verify the route resolves — the consumer may reject
        # due to enrollment checks, but it shouldn't 404.
        connected, code = await comm.connect()
        # Either connected or rejected with a known close code (not a routing error)
        await comm.disconnect()

    async def test_notifications_route_exists(self, user):
        """ws/notifications/ should be routable."""
        from backend_eva.asgi import application

        token = _make_jwt(user)
        comm = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )
        connected, _ = await comm.connect()
        assert connected is True
        await comm.disconnect()

    async def test_collab_route_exists(self, user):
        """ws/collab/<exercise_id>/<group_id>/ should be routable."""
        from backend_eva.asgi import application

        token = _make_jwt(user)
        comm = WebsocketCommunicator(
            application, f"/ws/collab/1/1/?token={token}"
        )
        connected, code = await comm.connect()
        # May reject due to group membership, but route should resolve
        await comm.disconnect()
