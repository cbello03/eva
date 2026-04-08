"""Tests for accounts Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from apps.accounts.schemas import RegisterIn, RoleChangeIn


class TestRegisterInValidation:
    def test_valid_input(self):
        r = RegisterIn(email="a@b.com", password="Abcdefg1", display_name="Test")
        assert r.email == "a@b.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="not-an-email", password="Abcdefg1", display_name="T")

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="a@b.com", password="Ab1", display_name="T")

    def test_no_uppercase_rejected(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="a@b.com", password="abcdefg1", display_name="T")

    def test_no_lowercase_rejected(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="a@b.com", password="ABCDEFG1", display_name="T")

    def test_no_digit_rejected(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="a@b.com", password="Abcdefgh", display_name="T")

    def test_empty_display_name_rejected(self):
        with pytest.raises(ValidationError):
            RegisterIn(email="a@b.com", password="Abcdefg1", display_name="   ")


class TestRoleChangeInValidation:
    def test_valid_roles(self):
        for role in ("student", "teacher", "admin"):
            assert RoleChangeIn(role=role).role == role

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            RoleChangeIn(role="superuser")
