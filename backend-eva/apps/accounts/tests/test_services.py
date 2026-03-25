"""Tests for AuthService — registration, login, logout, token refresh, role change."""

import jwt
import pytest
from django.conf import settings

from apps.accounts.models import RefreshToken, Role, User
from apps.accounts.schemas import LoginIn, RegisterIn
from apps.accounts.services import AuthService, JWT_ALGORITHM
from common.exceptions import DuplicateEmailError, InvalidCredentialsError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_user(
    email: str = "test@example.com",
    password: str = "StrongPass1",
    display_name: str = "Test User",
) -> User:
    return AuthService.register(
        RegisterIn(email=email, password=password, display_name=display_name)
    )


def _login_user(email: str = "test@example.com", password: str = "StrongPass1"):
    return AuthService.login(LoginIn(email=email, password=password))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_student(self):
        user = _register_user()
        assert user.role == Role.STUDENT
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_register_hashes_password(self):
        user = _register_user()
        assert user.password != "StrongPass1"
        assert user.password.startswith("pbkdf2_")

    def test_register_duplicate_email_raises(self):
        _register_user()
        with pytest.raises(DuplicateEmailError):
            _register_user()

    def test_register_normalizes_email(self):
        user = _register_user(email="Test@Example.COM")
        assert user.email == "test@example.com"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogin:
    def test_login_returns_token_pair(self):
        _register_user()
        pair = _login_user()
        assert pair.access_token
        assert pair.refresh_token

    def test_access_token_has_correct_claims(self):
        _register_user()
        pair = _login_user()
        payload = jwt.decode(
            pair.access_token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        assert payload["type"] == "access"
        assert payload["role"] == "student"
        assert "sub" in payload
        assert "exp" in payload

    def test_refresh_token_has_family_id(self):
        _register_user()
        pair = _login_user()
        payload = jwt.decode(
            pair.refresh_token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        assert payload["type"] == "refresh"
        assert "family_id" in payload

    def test_login_wrong_email_raises(self):
        _register_user()
        with pytest.raises(InvalidCredentialsError):
            AuthService.login(LoginIn(email="wrong@example.com", password="StrongPass1"))

    def test_login_wrong_password_raises(self):
        _register_user()
        with pytest.raises(InvalidCredentialsError):
            AuthService.login(LoginIn(email="test@example.com", password="WrongPass1"))

    def test_login_errors_are_indistinguishable(self):
        """Wrong email and wrong password produce the same error message."""
        _register_user()
        with pytest.raises(InvalidCredentialsError) as exc1:
            AuthService.login(LoginIn(email="wrong@example.com", password="StrongPass1"))
        with pytest.raises(InvalidCredentialsError) as exc2:
            AuthService.login(LoginIn(email="test@example.com", password="WrongPass1"))
        assert exc1.value.detail == exc2.value.detail
        assert exc1.value.status_code == exc2.value.status_code


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogout:
    def test_logout_revokes_refresh_token(self):
        _register_user()
        pair = _login_user()
        AuthService.logout(pair.refresh_token)
        # Attempting to refresh with the revoked token should fail
        with pytest.raises(InvalidCredentialsError):
            AuthService.refresh_tokens(pair.refresh_token)


# ---------------------------------------------------------------------------
# Token Refresh & Replay Detection
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_returns_new_tokens(self):
        _register_user()
        pair1 = _login_user()
        pair2 = AuthService.refresh_tokens(pair1.refresh_token)
        assert pair2.access_token != pair1.access_token
        assert pair2.refresh_token != pair1.refresh_token

    def test_old_refresh_token_invalid_after_rotation(self):
        _register_user()
        pair1 = _login_user()
        AuthService.refresh_tokens(pair1.refresh_token)
        # Old token should be rejected (it's been rotated out)
        with pytest.raises(InvalidCredentialsError):
            AuthService.refresh_tokens(pair1.refresh_token)

    def test_replay_detection_revokes_entire_family(self):
        """Reusing a rotated-out token invalidates the entire family."""
        _register_user()
        pair1 = _login_user()
        pair2 = AuthService.refresh_tokens(pair1.refresh_token)
        # Replay attack: reuse pair1's refresh token
        with pytest.raises(InvalidCredentialsError):
            AuthService.refresh_tokens(pair1.refresh_token)
        # Now pair2's token should also be invalid (family revoked)
        with pytest.raises(InvalidCredentialsError):
            AuthService.refresh_tokens(pair2.refresh_token)

    def test_new_refresh_token_is_valid(self):
        _register_user()
        pair1 = _login_user()
        pair2 = AuthService.refresh_tokens(pair1.refresh_token)
        # The new token should work
        pair3 = AuthService.refresh_tokens(pair2.refresh_token)
        assert pair3.access_token
        assert pair3.refresh_token

    def test_refresh_preserves_family_id(self):
        _register_user()
        pair1 = _login_user()
        p1 = jwt.decode(pair1.refresh_token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        pair2 = AuthService.refresh_tokens(pair1.refresh_token)
        p2 = jwt.decode(pair2.refresh_token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert p1["family_id"] == p2["family_id"]


# ---------------------------------------------------------------------------
# Role Change
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRoleChange:
    def test_change_role_updates_user(self):
        user = _register_user()
        updated = AuthService.change_role(user.pk, "teacher")
        assert updated.role == Role.TEACHER

    def test_change_role_invalidates_tokens(self):
        user = _register_user()
        pair = _login_user()
        AuthService.change_role(user.pk, "teacher")
        # All refresh tokens should be revoked
        assert not RefreshToken.objects.filter(user=user, is_revoked=False).exists()
        # Refreshing should fail
        with pytest.raises(InvalidCredentialsError):
            AuthService.refresh_tokens(pair.refresh_token)

    def test_change_role_nonexistent_user_raises(self):
        with pytest.raises(User.DoesNotExist):
            AuthService.change_role(99999, "admin")
