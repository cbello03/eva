"""Accounts app models — User, Role, and RefreshToken."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import TimestampedModel


class Role(models.TextChoices):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(AbstractUser):
    """Extended user model with email-based auth, role, and timezone."""

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    timezone = models.CharField(max_length=50, default="UTC")

    # Use email as the login identifier instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        db_table = "accounts_user"

    def __str__(self) -> str:
        return self.email


class RefreshToken(TimestampedModel):
    """Tracks refresh tokens for rotation and replay detection."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    family_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    is_revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "accounts_refresh_token"
        indexes = [
            models.Index(fields=["family_id", "is_revoked"]),
        ]

    def __str__(self) -> str:
        return f"RefreshToken(user={self.user_id}, family={self.family_id}, revoked={self.is_revoked})"
