"""
Unit tests for auth registration: service.py and router.py.

Uses AsyncMock and MagicMock to isolate all DB and external calls.
Does NOT require a live database connection.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from auth.schemas import RegisterRequest, TokenResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_uow(
    *,
    usuario_id: int = 1,
    rol_id: int = 10,
    rol_nombre: str = "CLIENT",
    rol_found: bool = True,
) -> MagicMock:
    """Build a mock UnitOfWork that simulates happy-path DB operations."""

    # Mock usuario returned after create
    mock_usuario = MagicMock()
    mock_usuario.id = usuario_id
    mock_usuario.email = "test@example.com"
    mock_usuario.nombre = "Juan"
    mock_usuario.apellido = None

    # Mock rol
    mock_rol = MagicMock() if rol_found else None
    if mock_rol is not None:
        mock_rol.id = rol_id
        mock_rol.nombre = rol_nombre

    # Mock refresh token record
    mock_refresh_token = MagicMock()

    # Build repository mocks
    mock_usuarios_repo = AsyncMock()
    mock_usuarios_repo.create.return_value = mock_usuario

    mock_roles_repo = AsyncMock()
    mock_roles_repo.find_by.return_value = mock_rol

    mock_usuario_roles_repo = AsyncMock()
    mock_usuario_roles_repo.create.return_value = MagicMock()

    mock_refresh_tokens_repo = AsyncMock()
    mock_refresh_tokens_repo.create.return_value = mock_refresh_token

    # Build UoW mock
    uow = MagicMock()
    uow.usuarios = mock_usuarios_repo
    uow.roles = mock_roles_repo
    uow.usuario_roles = mock_usuario_roles_repo
    uow.refresh_tokens = mock_refresh_tokens_repo

    return uow


def _make_register_request(**kwargs) -> RegisterRequest:
    defaults = {
        "email": "test@example.com",
        "password": "SecurePass1",
        "nombre": "Juan",
    }
    defaults.update(kwargs)
    return RegisterRequest(**defaults)


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestRegisterUserService:
    """Tests for auth.service.register_user."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_token_response(self):
        """register_user returns TokenResponse with non-empty tokens."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="hashed_pw") as mock_hash,
            patch("auth.service.create_access_token", return_value="access.token.here") as mock_access,
            patch("auth.service.create_refresh_token", return_value="refresh.token.here") as mock_refresh,
        ):
            result = await register_user(data, uow)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access.token.here"
        assert result.refresh_token == "refresh.token.here"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_password_is_hashed(self):
        """hash_password is called with the raw password from the request."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request(password="MySecret99")

        with (
            patch("auth.service.hash_password", return_value="bcrypt_hash") as mock_hash,
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        mock_hash.assert_called_once_with("MySecret99")

    @pytest.mark.asyncio
    async def test_usuario_created_with_hashed_password(self):
        """The Usuario passed to uow.usuarios.create must have hashed_password, not plain."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="HASHED"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        call_args = uow.usuarios.create.call_args
        created_usuario = call_args[0][0]  # first positional arg
        assert created_usuario.hashed_password == "HASHED"

    @pytest.mark.asyncio
    async def test_client_role_looked_up_from_db(self):
        """roles.find_by is called with nombre='CLIENT'."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        uow.roles.find_by.assert_called_once_with(nombre="CLIENT")

    @pytest.mark.asyncio
    async def test_usuario_rol_pivot_created(self):
        """UsuarioRol pivot is created with correct usuario_id and rol_id."""
        from auth.service import register_user

        uow = _make_uow(usuario_id=42, rol_id=7)
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        call_args = uow.usuario_roles.create.call_args
        pivot = call_args[0][0]
        assert pivot.usuario_id == 42
        assert pivot.rol_id == 7

    @pytest.mark.asyncio
    async def test_refresh_token_stored_in_db(self):
        """RefreshToken record is created with correct usuario_id and token."""
        from auth.service import register_user

        uow = _make_uow(usuario_id=5)
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt_string"),
        ):
            await register_user(data, uow)

        call_args = uow.refresh_tokens.create.call_args
        rt_record = call_args[0][0]
        assert rt_record.usuario_id == 5
        assert rt_record.token == "rt_string"

    @pytest.mark.asyncio
    async def test_refresh_token_expires_at_is_7_days(self):
        """RefreshToken.expires_at is approximately now + 7 days."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        call_args = uow.refresh_tokens.create.call_args
        rt_record = call_args[0][0]

        expected_min = datetime.utcnow() + timedelta(days=6, hours=23)
        expected_max = datetime.utcnow() + timedelta(days=7, hours=1)
        assert expected_min <= rt_record.expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_access_token_payload_includes_email_and_roles(self):
        """create_access_token is called with email and roles=['CLIENT'] in data dict."""
        from auth.service import register_user

        uow = _make_uow(usuario_id=99)
        uow.usuarios.create.return_value.email = "alice@example.com"
        data = _make_register_request(email="alice@example.com")

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at") as mock_access,
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        call_kwargs = mock_access.call_args[1] if mock_access.call_args[1] else {}
        call_data = mock_access.call_args[0][0] if mock_access.call_args[0] else call_kwargs.get("data", {})
        assert call_data.get("email") == "alice@example.com"
        assert call_data.get("roles") == ["CLIENT"]

    @pytest.mark.asyncio
    async def test_missing_client_role_raises_500(self):
        """If CLIENT role is absent from DB, HTTPException 500 is raised."""
        from auth.service import register_user
        from fastapi import HTTPException

        uow = _make_uow(rol_found=False)
        data = _make_register_request()

        with (
            patch("auth.service.hash_password", return_value="h"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await register_user(data, uow)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_apellido_optional_creates_user(self):
        """Registering without apellido should work fine."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request(nombre="Pedro")  # no apellido

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            result = await register_user(data, uow)

        assert isinstance(result, TokenResponse)

    @pytest.mark.asyncio
    async def test_apellido_passed_to_usuario_model(self):
        """Apellido from RegisterRequest is passed to the Usuario being created."""
        from auth.service import register_user

        uow = _make_uow()
        data = _make_register_request(nombre="Ana", apellido="García")

        with (
            patch("auth.service.hash_password", return_value="h"),
            patch("auth.service.create_access_token", return_value="at"),
            patch("auth.service.create_refresh_token", return_value="rt"),
        ):
            await register_user(data, uow)

        call_args = uow.usuarios.create.call_args
        created_usuario = call_args[0][0]
        assert created_usuario.apellido == "García"


# ---------------------------------------------------------------------------
# Schema integration (double-check constraints the router delegates to Pydantic)
# ---------------------------------------------------------------------------

class TestRegisterRequestConstraints:
    """Verify that schema constraints align with business rules."""

    def test_password_min_8_chars(self):
        """Password must be >= 8 chars."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="short", nombre="Juan")

    def test_nombre_min_1_char(self):
        """Nombre must be at least 1 char."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="password123", nombre="")

    def test_valid_request_accepted(self):
        req = RegisterRequest(
            email="alice@example.com",
            password="securePass99",
            nombre="Alice",
            apellido="Smith",
        )
        assert req.nombre == "Alice"
        assert req.apellido == "Smith"
