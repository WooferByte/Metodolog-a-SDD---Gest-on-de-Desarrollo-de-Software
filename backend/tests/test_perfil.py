"""
Unit tests for perfil endpoints: schemas, service functions.

Uses AsyncMock and MagicMock to isolate all DB and external calls.
Does NOT require a live database connection.

Covers:
- TestGetPerfilService    — get_perfil returns UsuarioResponse
- TestUpdatePerfilService — update_perfil patches correct fields
- TestCambiarPasswordService — password change + refresh token revocation
- TestPerfilSchemas       — PerfilUpdate and CambiarPasswordRequest validation
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from usuarios.perfil_schemas import CambiarPasswordRequest, PerfilUpdate
from usuarios.schemas import UsuarioResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_usuario(
    *,
    id: int = 1,
    email: str = "test@example.com",
    hashed_password: str = "hashed_pw",
    nombre: str = "Juan",
    apellido: str | None = "Pérez",
    activo: bool = True,
    telefono: str | None = "1122334455",
) -> MagicMock:
    """Build a mock Usuario with the same fields as the real model."""
    mock = MagicMock()
    mock.id = id
    mock.email = email
    mock.hashed_password = hashed_password
    mock.nombre = nombre
    mock.apellido = apellido
    mock.activo = activo
    mock.telefono = telefono
    mock.creado_en = datetime.utcnow()
    return mock


def _make_uow(
    *,
    refresh_tokens: list | None = None,
) -> MagicMock:
    """Build a mock UnitOfWork with usuarios and refresh_tokens repos."""
    uow = MagicMock()

    # usuarios repo
    usuarios_repo = AsyncMock()
    usuarios_repo.update = AsyncMock(return_value=None)
    uow.usuarios = usuarios_repo

    # refresh_tokens repo
    rt_repo = AsyncMock()
    rt_repo.find_all_by = AsyncMock(return_value=refresh_tokens or [])
    rt_repo.update = AsyncMock(return_value=None)
    uow.refresh_tokens = rt_repo

    return uow


def _make_mock_refresh_token(*, revoked_at: datetime | None = None) -> MagicMock:
    """Build a mock RefreshToken."""
    token = MagicMock()
    token.revoked_at = revoked_at
    return token


# ---------------------------------------------------------------------------
# TestGetPerfilService
# ---------------------------------------------------------------------------


class TestGetPerfilService:
    """Tests for perfil_service.get_perfil."""

    @pytest.mark.asyncio
    async def test_get_perfil_returns_usuario_response(self):
        """get_perfil returns a UsuarioResponse populated from the user object."""
        from usuarios.perfil_service import get_perfil

        mock_user = _make_mock_usuario()

        with patch(
            "usuarios.perfil_service.UsuarioResponse.model_validate"
        ) as mock_validate:
            expected = MagicMock(spec=UsuarioResponse)
            mock_validate.return_value = expected

            result = await get_perfil(mock_user)

        mock_validate.assert_called_once_with(mock_user)
        assert result is expected


# ---------------------------------------------------------------------------
# TestUpdatePerfilService
# ---------------------------------------------------------------------------


class TestUpdatePerfilService:
    """Tests for perfil_service.update_perfil."""

    @pytest.mark.asyncio
    async def test_update_nombre_only(self):
        """Only nombre is patched; telefono is left unchanged."""
        from usuarios.perfil_service import update_perfil

        mock_user = _make_mock_usuario(nombre="Juan", telefono="111")
        uow = _make_uow()
        data = PerfilUpdate(nombre="Carlos")

        with patch("usuarios.perfil_service.UsuarioResponse.model_validate") as mock_validate:
            mock_validate.return_value = MagicMock(spec=UsuarioResponse)
            await update_perfil(mock_user, data, uow)

        assert mock_user.nombre == "Carlos"
        # telefono not touched — still "111"
        assert mock_user.telefono == "111"
        uow.usuarios.update.assert_awaited_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_telefono_only(self):
        """Only telefono is patched; nombre is left unchanged."""
        from usuarios.perfil_service import update_perfil

        mock_user = _make_mock_usuario(nombre="Juan", telefono="111")
        uow = _make_uow()
        data = PerfilUpdate(telefono="999")

        with patch("usuarios.perfil_service.UsuarioResponse.model_validate") as mock_validate:
            mock_validate.return_value = MagicMock(spec=UsuarioResponse)
            await update_perfil(mock_user, data, uow)

        assert mock_user.telefono == "999"
        assert mock_user.nombre == "Juan"
        uow.usuarios.update.assert_awaited_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_both_fields(self):
        """Both nombre and telefono are patched correctly."""
        from usuarios.perfil_service import update_perfil

        mock_user = _make_mock_usuario(nombre="Juan", telefono="111")
        uow = _make_uow()
        data = PerfilUpdate(nombre="Carlos", telefono="222")

        with patch("usuarios.perfil_service.UsuarioResponse.model_validate") as mock_validate:
            mock_validate.return_value = MagicMock(spec=UsuarioResponse)
            await update_perfil(mock_user, data, uow)

        assert mock_user.nombre == "Carlos"
        assert mock_user.telefono == "222"
        uow.usuarios.update.assert_awaited_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_returns_usuario_response(self):
        """update_perfil returns an instance of UsuarioResponse."""
        from usuarios.perfil_service import update_perfil

        mock_user = _make_mock_usuario()
        uow = _make_uow()
        data = PerfilUpdate(nombre="Nuevo")

        with patch("usuarios.perfil_service.UsuarioResponse.model_validate") as mock_validate:
            expected = MagicMock(spec=UsuarioResponse)
            mock_validate.return_value = expected
            result = await update_perfil(mock_user, data, uow)

        assert result is expected


# ---------------------------------------------------------------------------
# TestCambiarPasswordService
# ---------------------------------------------------------------------------


class TestCambiarPasswordService:
    """Tests for perfil_service.cambiar_password."""

    @pytest.mark.asyncio
    async def test_wrong_password_raises_400(self):
        """verify_password returning False raises HTTPException 400."""
        from usuarios.perfil_service import cambiar_password

        mock_user = _make_mock_usuario()
        uow = _make_uow()
        data = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )

        with patch("usuarios.perfil_service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await cambiar_password(mock_user, data, uow)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["detail"] == "Contraseña actual incorrecta"
        assert exc_info.value.detail["status"] == 400

    @pytest.mark.asyncio
    async def test_correct_password_hashes_new_password(self):
        """verify_password True → hash_password is called with nueva_password."""
        from usuarios.perfil_service import cambiar_password

        mock_user = _make_mock_usuario()
        uow = _make_uow()
        data = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )

        with (
            patch("usuarios.perfil_service.verify_password", return_value=True),
            patch("usuarios.perfil_service.hash_password", return_value="new_hash") as mock_hash,
        ):
            await cambiar_password(mock_user, data, uow)

        mock_hash.assert_called_once_with("NewPassword2")
        assert mock_user.hashed_password == "new_hash"

    @pytest.mark.asyncio
    async def test_correct_password_calls_uow_update(self):
        """uow.usuarios.update is called with current_user after password hash."""
        from usuarios.perfil_service import cambiar_password

        mock_user = _make_mock_usuario()
        uow = _make_uow()
        data = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )

        with (
            patch("usuarios.perfil_service.verify_password", return_value=True),
            patch("usuarios.perfil_service.hash_password", return_value="new_hash"),
        ):
            await cambiar_password(mock_user, data, uow)

        uow.usuarios.update.assert_awaited_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_revokes_all_active_refresh_tokens(self):
        """All active tokens (revoked_at is None) are revoked via uow.refresh_tokens.update."""
        from usuarios.perfil_service import cambiar_password

        mock_user = _make_mock_usuario(id=7)
        active_token_1 = _make_mock_refresh_token(revoked_at=None)
        active_token_2 = _make_mock_refresh_token(revoked_at=None)
        uow = _make_uow(refresh_tokens=[active_token_1, active_token_2])
        data = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )

        with (
            patch("usuarios.perfil_service.verify_password", return_value=True),
            patch("usuarios.perfil_service.hash_password", return_value="h"),
        ):
            await cambiar_password(mock_user, data, uow)

        uow.refresh_tokens.find_all_by.assert_awaited_once_with(usuario_id=7)
        assert uow.refresh_tokens.update.await_count == 2
        assert active_token_1.revoked_at is not None
        assert active_token_2.revoked_at is not None

    @pytest.mark.asyncio
    async def test_already_revoked_tokens_not_updated(self):
        """Tokens with revoked_at already set are skipped — not passed to update."""
        from usuarios.perfil_service import cambiar_password

        mock_user = _make_mock_usuario(id=3)
        already_revoked = _make_mock_refresh_token(revoked_at=datetime(2026, 1, 1))
        active_token = _make_mock_refresh_token(revoked_at=None)
        uow = _make_uow(refresh_tokens=[already_revoked, active_token])
        data = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )

        with (
            patch("usuarios.perfil_service.verify_password", return_value=True),
            patch("usuarios.perfil_service.hash_password", return_value="h"),
        ):
            await cambiar_password(mock_user, data, uow)

        # Only the active token should have been passed to update
        assert uow.refresh_tokens.update.await_count == 1
        # already_revoked.revoked_at should not have changed
        assert already_revoked.revoked_at == datetime(2026, 1, 1)
        assert active_token.revoked_at is not None

    @pytest.mark.asyncio
    async def test_returns_none_on_success(self):
        """cambiar_password returns None on success (router sends 204)."""
        from usuarios.perfil_service import cambiar_password

        mock_user = _make_mock_usuario()
        uow = _make_uow()
        data = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )

        with (
            patch("usuarios.perfil_service.verify_password", return_value=True),
            patch("usuarios.perfil_service.hash_password", return_value="h"),
        ):
            result = await cambiar_password(mock_user, data, uow)

        assert result is None


# ---------------------------------------------------------------------------
# TestPerfilSchemas
# ---------------------------------------------------------------------------


class TestPerfilSchemas:
    """Tests for PerfilUpdate and CambiarPasswordRequest validation."""

    def test_perfil_update_empty_raises_validation_error(self):
        """PerfilUpdate() with no fields raises ValidationError."""
        with pytest.raises(ValidationError):
            PerfilUpdate()

    def test_perfil_update_none_fields_raises_validation_error(self):
        """PerfilUpdate(nombre=None, telefono=None) raises ValidationError."""
        with pytest.raises(ValidationError):
            PerfilUpdate(nombre=None, telefono=None)

    def test_perfil_update_nombre_only_is_valid(self):
        """PerfilUpdate with only nombre is valid."""
        p = PerfilUpdate(nombre="Ana")
        assert p.nombre == "Ana"
        assert p.telefono is None

    def test_perfil_update_telefono_only_is_valid(self):
        """PerfilUpdate with only telefono is valid."""
        p = PerfilUpdate(telefono="123456")
        assert p.telefono == "123456"
        assert p.nombre is None

    def test_cambiar_password_same_passwords_raises_validation_error(self):
        """password_actual == nueva_password raises ValidationError (422 in API)."""
        with pytest.raises(ValidationError):
            CambiarPasswordRequest(
                password_actual="SamePass1",
                nueva_password="SamePass1",
            )

    def test_cambiar_password_min_length(self):
        """nueva_password with 7 characters raises ValidationError."""
        with pytest.raises(ValidationError):
            CambiarPasswordRequest(
                password_actual="OldPass12",
                nueva_password="Short1",
            )

    def test_cambiar_password_current_min_length(self):
        """password_actual with 7 characters raises ValidationError."""
        with pytest.raises(ValidationError):
            CambiarPasswordRequest(
                password_actual="Short1",
                nueva_password="NewPass12",
            )

    def test_cambiar_password_valid(self):
        """Valid CambiarPasswordRequest passes all validators."""
        req = CambiarPasswordRequest(
            password_actual="OldPassword1",
            nueva_password="NewPassword2",
        )
        assert req.password_actual == "OldPassword1"
        assert req.nueva_password == "NewPassword2"

    def test_perfil_update_nombre_sanitized(self):
        """nombre containing HTML tags is sanitized (tags stripped)."""
        p = PerfilUpdate(nombre="<script>alert('xss')</script>Juan")
        # dangerous block stripped, then remaining tags stripped
        assert "<" not in p.nombre
        assert "script" not in p.nombre
        assert "Juan" in p.nombre

    def test_perfil_update_nombre_max_length(self):
        """nombre longer than 100 characters raises ValidationError."""
        with pytest.raises(ValidationError):
            PerfilUpdate(nombre="a" * 101)

    def test_perfil_update_telefono_max_length(self):
        """telefono longer than 20 characters raises ValidationError."""
        with pytest.raises(ValidationError):
            PerfilUpdate(telefono="1" * 21)
