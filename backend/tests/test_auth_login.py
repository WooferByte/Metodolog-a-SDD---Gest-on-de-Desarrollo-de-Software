"""
Unit tests for auth login: service.py login_user function.

Uses AsyncMock and MagicMock to isolate all DB and external calls.
Does NOT require a live database connection.

Security scenarios tested:
- Successful login returns TokenResponse with tokens + user
- Wrong password → 401 "Invalid credentials"
- Unknown email → 401 "Invalid credentials"  (same response, no enumeration)
- RefreshToken row is created on successful login
- Access token payload contains sub, email, roles
"""
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest

from fastapi import HTTPException

from auth.schemas import LoginRequest, TokenResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_usuario(
    *,
    id: int = 1,
    email: str = "test@example.com",
    hashed_password: str = "hashed_pw",
    nombre: str = "Juan",
    apellido: str | None = None,
    activo: bool = True,
    telefono: str | None = None,
    roles: list | None = None,
) -> MagicMock:
    """Build a mock Usuario object."""
    mock = MagicMock()
    mock.id = id
    mock.email = email
    mock.hashed_password = hashed_password
    mock.nombre = nombre
    mock.apellido = apellido
    mock.activo = activo
    mock.telefono = telefono
    mock.creado_en = datetime.now(UTC)

    if roles is None:
        mock_rol = MagicMock()
        mock_rol.nombre = "CLIENT"
        mock.roles = [mock_rol]
    else:
        mock.roles = roles

    return mock


def _make_uow(*, usuario: MagicMock | None = None) -> MagicMock:
    """Build a mock UnitOfWork."""
    mock_usuarios_repo = AsyncMock()
    mock_usuarios_repo.find_by.return_value = usuario

    mock_refresh_tokens_repo = AsyncMock()
    mock_refresh_tokens_repo.create.return_value = MagicMock()

    uow = MagicMock()
    uow.usuarios = mock_usuarios_repo
    uow.refresh_tokens = mock_refresh_tokens_repo
    return uow


def _make_login_request(**kwargs) -> LoginRequest:
    defaults = {
        "email": "test@example.com",
        "password": "SecurePass1",
    }
    defaults.update(kwargs)
    return LoginRequest(**defaults)


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestLoginUserService:
    """Tests for auth.service.login_user."""

    @pytest.mark.asyncio
    async def test_successful_login_returns_token_response(self):
        """login_user returns TokenResponse with access_token, refresh_token, usuario."""
        from auth.service import login_user

        mock_usuario = _make_mock_usuario()
        uow = _make_uow(usuario=mock_usuario)
        data = _make_login_request()

        with (
            patch("auth.service.verify_password", return_value=True),
            patch("auth.service.create_access_token", return_value="access.token"),
            patch("auth.service.create_refresh_token", return_value="refresh.token"),
            patch("auth.service.UsuarioResponse.model_validate") as mock_validate,
        ):
            mock_validate.return_value = MagicMock()
            result = await login_user(data, uow)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access.token"
        assert result.refresh_token == "refresh.token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_wrong_password_raises_401(self):
        """login_user raises HTTPException 401 when password is wrong."""
        from auth.service import login_user

        mock_usuario = _make_mock_usuario()
        uow = _make_uow(usuario=mock_usuario)
        data = _make_login_request(password="WrongPassword1")

        with patch("auth.service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await login_user(data, uow)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_unknown_email_raises_401(self):
        """login_user raises HTTPException 401 when email is not found in DB."""
        from auth.service import login_user

        uow = _make_uow(usuario=None)  # user not found
        data = _make_login_request(email="ghost@example.com")

        with patch("auth.service.verify_password", return_value=False) as mock_verify:
            with pytest.raises(HTTPException) as exc_info:
                await login_user(data, uow)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_unknown_email_still_calls_verify_password_for_timing(self):
        """When user not found, verify_password is still called against DUMMY_HASH."""
        from auth.service import login_user, DUMMY_HASH

        uow = _make_uow(usuario=None)
        data = _make_login_request(email="nobody@example.com")

        with patch("auth.service.verify_password", return_value=False) as mock_verify:
            with pytest.raises(HTTPException):
                await login_user(data, uow)

        # Must have been called with the dummy hash to prevent timing attacks
        mock_verify.assert_called_once_with(data.password, DUMMY_HASH)

    @pytest.mark.asyncio
    async def test_refresh_token_row_created_on_successful_login(self):
        """RefreshToken record is created in DB on successful login."""
        from auth.service import login_user
        from core.models import RefreshToken

        mock_usuario = _make_mock_usuario(id=42)
        uow = _make_uow(usuario=mock_usuario)
        data = _make_login_request()

        with (
            patch("auth.service.verify_password", return_value=True),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt_string"),
            patch("auth.service.UsuarioResponse.model_validate", return_value=MagicMock()),
        ):
            await login_user(data, uow)

        uow.refresh_tokens.create.assert_called_once()
        call_args = uow.refresh_tokens.create.call_args
        rt_record = call_args[0][0]
        assert rt_record.usuario_id == 42
        assert rt_record.token == "rt_string"

    @pytest.mark.asyncio
    async def test_refresh_token_expires_at_is_7_days(self):
        """RefreshToken.expires_at is approximately now + 7 days."""
        from auth.service import login_user

        mock_usuario = _make_mock_usuario(id=5)
        uow = _make_uow(usuario=mock_usuario)
        data = _make_login_request()

        with (
            patch("auth.service.verify_password", return_value=True),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
            patch("auth.service.UsuarioResponse.model_validate", return_value=MagicMock()),
        ):
            await login_user(data, uow)

        call_args = uow.refresh_tokens.create.call_args
        rt_record = call_args[0][0]

        expected_min = datetime.now(UTC) + timedelta(days=6, hours=23)
        expected_max = datetime.now(UTC) + timedelta(days=7, hours=1)
        assert expected_min <= rt_record.expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_access_token_payload_contains_sub_email_roles(self):
        """create_access_token is called with sub=str(user_id), email, roles list."""
        from auth.service import login_user

        mock_rol = MagicMock()
        mock_rol.nombre = "ADMIN"
        mock_usuario = _make_mock_usuario(id=99, email="admin@example.com", roles=[mock_rol])
        uow = _make_uow(usuario=mock_usuario)
        data = _make_login_request(email="admin@example.com")

        with (
            patch("auth.service.verify_password", return_value=True),
            patch("auth.service.create_access_token", return_value="at") as mock_access,
            patch("auth.service.create_refresh_token", return_value="rt"),
            patch("auth.service.UsuarioResponse.model_validate", return_value=MagicMock()),
        ):
            await login_user(data, uow)

        call_data = mock_access.call_args[1].get("data") or mock_access.call_args[0][0]
        assert call_data["sub"] == "99"
        assert call_data["email"] == "admin@example.com"
        assert call_data["roles"] == ["ADMIN"]

    @pytest.mark.asyncio
    async def test_unknown_and_wrong_password_return_same_error(self):
        """Both unknown email and wrong password return HTTP 401 with same detail."""
        from auth.service import login_user

        # Test unknown email
        uow_no_user = _make_uow(usuario=None)
        with patch("auth.service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc1:
                await login_user(_make_login_request(email="ghost@x.com"), uow_no_user)

        # Test wrong password
        mock_usuario = _make_mock_usuario()
        uow_wrong_pw = _make_uow(usuario=mock_usuario)
        with patch("auth.service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc2:
                await login_user(_make_login_request(password="wrong"), uow_wrong_pw)

        assert exc1.value.status_code == exc2.value.status_code == 401
        assert exc1.value.detail == exc2.value.detail == "Invalid credentials"
