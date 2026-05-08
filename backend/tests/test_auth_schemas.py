"""
Unit tests for backend/auth/schemas.py — LoginRequest, RegisterRequest, TokenResponse, RefreshRequest.
"""
import pytest
from pydantic import ValidationError

from auth.schemas import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest


class TestLoginRequest:
    """Tests for LoginRequest schema."""

    def test_valid_login(self):
        """Valid email and non-empty password should be accepted."""
        req = LoginRequest(email="user@example.com", password="secret")
        assert req.email == "user@example.com"
        assert req.password == "secret"

    def test_invalid_email_rejected(self):
        """Malformed email should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="not-an-email", password="secret")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_empty_password_rejected(self):
        """Empty password should raise ValidationError (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="user@example.com", password="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)


class TestRegisterRequest:
    """Tests for RegisterRequest schema."""

    def test_valid_register(self):
        """Valid fields should be accepted."""
        req = RegisterRequest(
            email="new@example.com",
            password="securePass1",
            nombre="Juan",
        )
        assert req.nombre == "Juan"
        assert req.apellido is None

    def test_short_password_rejected(self):
        """Password shorter than 8 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(email="a@b.com", password="short", nombre="Juan")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_long_password_rejected(self):
        """Password longer than 128 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(email="a@b.com", password="x" * 129, nombre="Juan")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_empty_nombre_rejected(self):
        """Empty nombre should raise ValidationError (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(email="a@b.com", password="password123", nombre="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("nombre",) for e in errors)

    def test_nombre_sanitized_script_tag(self):
        """Script tags in nombre should be stripped."""
        req = RegisterRequest(
            email="a@b.com",
            password="password123",
            nombre="<script>evil()</script>Juan",
        )
        assert req.nombre == "Juan"

    def test_apellido_sanitized(self):
        """HTML tags in apellido should be stripped."""
        req = RegisterRequest(
            email="a@b.com",
            password="password123",
            nombre="Juan",
            apellido="<b>García</b>",
        )
        assert req.apellido == "García"

    def test_invalid_email_rejected(self):
        """Invalid email in register should raise ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(email="bad-email", password="password123", nombre="Juan")


class TestTokenResponse:
    """Tests for TokenResponse schema."""

    def test_default_token_type(self):
        """token_type should default to 'bearer'."""
        resp = TokenResponse(access_token="acc", refresh_token="ref")
        assert resp.token_type == "bearer"

    def test_custom_token_type(self):
        """token_type can be overridden."""
        resp = TokenResponse(access_token="acc", refresh_token="ref", token_type="custom")
        assert resp.token_type == "custom"


class TestRefreshRequest:
    """Tests for RefreshRequest schema."""

    def test_valid_refresh(self):
        req = RefreshRequest(refresh_token="some-token")
        assert req.refresh_token == "some-token"

    def test_empty_refresh_token_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RefreshRequest(refresh_token="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("refresh_token",) for e in errors)
