"""Accounts app Pydantic schemas for request/response validation."""

import re

from ninja import Schema
from pydantic import field_validator


class RegisterIn(Schema):
    """Registration request payload."""

    email: str
    password: str
    display_name: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one numeric character")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Display name is required")
        if len(v) > 100:
            raise ValueError("Display name must be at most 100 characters")
        return v


class LoginIn(Schema):
    """Login request payload."""

    email: str
    password: str


class TokenOut(Schema):
    """Response containing the access token."""

    access_token: str


class UserOut(Schema):
    """Public user representation."""

    id: int
    email: str
    display_name: str
    role: str
    timezone: str


class RoleChangeIn(Schema):
    """Payload for changing a user's role."""

    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"student", "teacher", "admin"}
        if v.lower() not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return v.lower()
