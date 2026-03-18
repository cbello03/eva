"""AuthService — authentication and authorization business logic."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError

from apps.accounts.models import RefreshToken, Role, User
from apps.accounts.schemas import LoginIn, RegisterIn
from common.exceptions import DuplicateEmailError, InvalidCredentialsError

# Token lifetimes
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

JWT_ALGORITHM = "HS256"


@dataclass
class TokenPair:
    """Holds an access + refresh token pair."""

    access_token: str
    refresh_token: str


class AuthService:
    """Handles registration, login, logout, token refresh, and role changes."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    @staticmethod
    def register(data: RegisterIn) -> User:
        """Create a new Student account.

        Raises:
            DuplicateEmailError: if the email is already taken.
        """
        if User.objects.filter(email=data.email).exists():
            raise DuplicateEmailError()

        try:
            user = User(
                email=data.email,
                display_name=data.display_name,
                role=Role.STUDENT,
                username=data.email,  # AbstractUser requires username
            )
            user.password = make_password(data.password)
            user.save()
        except IntegrityError:
            raise DuplicateEmailError()

        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    @staticmethod
    def login(data: LoginIn) -> TokenPair:
        """Authenticate credentials and return a token pair.

        Raises:
            InvalidCredentialsError: on wrong email or wrong password
                (same message for both to avoid user enumeration).
        """
        try:
            user = User.objects.get(email=data.email)
        except User.DoesNotExist:
            raise InvalidCredentialsError()

        if not check_password(data.password, user.password):
            raise InvalidCredentialsError()

        return AuthService._issue_token_pair(user)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------
    @staticmethod
    def logout(refresh_token_raw: str) -> None:
        """Revoke the given refresh token."""
        token_hash = AuthService._hash_token(refresh_token_raw)
        RefreshToken.objects.filter(token_hash=token_hash).update(is_revoked=True)

    # ------------------------------------------------------------------
    # Token refresh with replay detection
    # ------------------------------------------------------------------
    @staticmethod
    def refresh_tokens(refresh_token_raw: str) -> TokenPair:
        """Rotate tokens. Detects replay attacks via family_id.

        Raises:
            InvalidCredentialsError: if the token is invalid, expired,
                revoked, or a replay is detected.
        """
        # Decode without verifying expiry first so we can read claims
        try:
            payload = jwt.decode(
                refresh_token_raw,
                settings.SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["sub", "family_id", "exp", "type"]},
            )
        except jwt.PyJWTError:
            raise InvalidCredentialsError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise InvalidCredentialsError("Invalid token type")

        token_hash = AuthService._hash_token(refresh_token_raw)

        try:
            stored = RefreshToken.objects.select_related("user").get(
                token_hash=token_hash,
            )
        except RefreshToken.DoesNotExist:
            # Token not found — could be a replay of a rotated-out token.
            # Revoke the entire family as a precaution.
            family_id = payload.get("family_id")
            if family_id:
                RefreshToken.objects.filter(family_id=family_id).update(
                    is_revoked=True,
                )
            raise InvalidCredentialsError("Invalid refresh token")

        # If the stored token is already revoked, this is a replay attack.
        # Revoke the entire family.
        if stored.is_revoked:
            RefreshToken.objects.filter(family_id=stored.family_id).update(
                is_revoked=True,
            )
            raise InvalidCredentialsError("Token reuse detected")

        if stored.expires_at < datetime.now(timezone.utc):
            raise InvalidCredentialsError("Refresh token expired")

        # Revoke the current token (it's been used)
        stored.is_revoked = True
        stored.save(update_fields=["is_revoked"])

        # Issue a new pair in the same family
        return AuthService._issue_token_pair(stored.user, family_id=stored.family_id)

    # ------------------------------------------------------------------
    # Role change (Admin only — enforced at API layer)
    # ------------------------------------------------------------------
    @staticmethod
    def change_role(target_user_id: int, new_role: str) -> User:
        """Update a user's role and invalidate all their refresh tokens.

        Raises:
            User.DoesNotExist: if the target user is not found.
        """
        user = User.objects.get(pk=target_user_id)
        user.role = new_role
        user.save(update_fields=["role"])

        # Invalidate every refresh token so the user must re-authenticate
        RefreshToken.objects.filter(user=user, is_revoked=False).update(
            is_revoked=True,
        )

        return user

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _issue_token_pair(
        user: User,
        family_id: uuid.UUID | None = None,
    ) -> TokenPair:
        """Create a signed access + refresh token pair and persist the
        refresh token hash."""
        now = datetime.now(timezone.utc)
        if family_id is None:
            family_id = uuid.uuid4()

        # Access token (short-lived, includes role claim)
        access_payload = {
            "sub": str(user.pk),
            "role": user.role,
            "type": "access",
            "iat": now,
            "exp": now + ACCESS_TOKEN_LIFETIME,
        }
        access_token = jwt.encode(
            access_payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM,
        )

        # Refresh token (long-lived, includes family_id for replay detection)
        refresh_payload = {
            "sub": str(user.pk),
            "family_id": str(family_id),
            "type": "refresh",
            "iat": now,
            "exp": now + REFRESH_TOKEN_LIFETIME,
        }
        refresh_token = jwt.encode(
            refresh_payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM,
        )

        # Persist the refresh token hash
        RefreshToken.objects.create(
            user=user,
            token_hash=AuthService._hash_token(refresh_token),
            family_id=family_id,
            expires_at=now + REFRESH_TOKEN_LIFETIME,
        )

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """SHA-256 hash of a raw JWT string."""
        return hashlib.sha256(raw_token.encode()).hexdigest()
