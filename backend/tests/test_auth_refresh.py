"""
Unit tests for auth token refresh: service.py refresh_token_service function.

Uses AsyncMock and MagicMock to isolate all DB and external calls.
Does NOT require a live database connection.

Security scenarios tested:
- Unknown token → 401 "Invalid refresh token"
- Revoked token (replay attack) → 401 + all tokens for user revoked
- Expired token → 401 "Refresh token expired"
- Valid token → 200 with new token pair, old token revoked
- Valid token → new access token payload has correct sub, email, roles
"""
from datetime import datetime, timedelta, UTC, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from fastapi import HTTPException

from auth.schemas import RefreshRequest, TokenResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_refresh_token_record(
    *,
    id: int = 10,
    usuario_id: int = 1,
    token: str = "old.refresh.token",
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> MagicMock:
    """Build a mock RefreshToken DB record."""
    mock = MagicMock()
    mock.id = id
    mock.usuario_id = usuario_id
    mock.token = token
    mock.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=7))
    mock.revoked_at = revoked_at
    return mock


def _make_mock_usuario(
    *,
    id: int = 1,
    email: str = "test@example.com",
    roles: list | None = None,
) -> MagicMock:
    """Build a mock Usuario object."""
    mock = MagicMock()
    mock.id = id
    mock.email = email
    if roles is None:
        mock_rol = MagicMock()
        mock_rol.nombre = "CLIENT"
        mock.roles = [mock_rol]
    else:
        mock.roles = roles
    return mock


def _make_uow(
    *,
    token_record: MagicMock | None = None,
    usuario: MagicMock | None = None,
    all_tokens: list | None = None,
) -> MagicMock:
    """Build a mock UnitOfWork with refresh_tokens and usuarios repos."""
    mock_refresh_repo = AsyncMock()
    mock_refresh_repo.find_by.return_value = token_record
    mock_refresh_repo.find_all_by.return_value = all_tokens or []
    mock_refresh_repo.update.return_value = token_record
    mock_refresh_repo.create.return_value = MagicMock()

    mock_usuarios_repo = AsyncMock()
    mock_usuarios_repo.get_by_id.return_value = usuario

    uow = MagicMock()
    uow.refresh_tokens = mock_refresh_repo
    uow.usuarios = mock_usuarios_repo
    return uow


def _make_refresh_request(refresh_token: str = "old.refresh.token") -> RefreshRequest:
    return RefreshRequest(refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestRefreshTokenService:
    """Tests for auth.service.refresh_token_service."""

    @pytest.mark.asyncio
    async def test_unknown_token_raises_401(self):
        """Unknown token → 401 'Invalid refresh token'."""
        from auth.service import refresh_token_service

        uow = _make_uow(token_record=None)
        data = _make_refresh_request("totally.unknown.token")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token_service(data, uow)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_revoked_token_triggers_replay_attack_response(self):
        """Revoked token → 401 'Replay attack detected — all sessions revoked'."""
        from auth.service import refresh_token_service

        revoked_record = _make_refresh_token_record(
            revoked_at=datetime.now(UTC) - timedelta(minutes=5)
        )
        # One active sibling token that should get revoked
        sibling = _make_refresh_token_record(id=11, token="sibling.token", revoked_at=None)
        uow = _make_uow(
            token_record=revoked_record,
            all_tokens=[revoked_record, sibling],
        )
        data = _make_refresh_request()

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token_service(data, uow)

        assert exc_info.value.status_code == 401
        assert "Replay attack" in exc_info.value.detail
        # update should have been called for the sibling (revoked_at=None)
        uow.refresh_tokens.update.assert_awaited()

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        """Expired token (expires_at in the past) → 401 'Refresh token expired'."""
        from auth.service import refresh_token_service

        expired_record = _make_refresh_token_record(
            expires_at=datetime.now(UTC) - timedelta(days=1),
            revoked_at=None,
        )
        uow = _make_uow(token_record=expired_record)
        data = _make_refresh_request()

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token_service(data, uow)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Refresh token expired"

    @pytest.mark.asyncio
    async def test_expired_naive_datetime_token_raises_401(self):
        """Expired token stored as naive datetime (UTC) → 401 'Refresh token expired'."""
        from auth.service import refresh_token_service

        # naive datetime = no tzinfo — service must handle this
        naive_past = datetime.utcnow() - timedelta(days=1)
        expired_record = _make_refresh_token_record(
            expires_at=naive_past,
            revoked_at=None,
        )
        uow = _make_uow(token_record=expired_record)
        data = _make_refresh_request()

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token_service(data, uow)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Refresh token expired"

    @pytest.mark.asyncio
    async def test_valid_token_returns_new_token_pair(self):
        """Valid token → 200 with new access_token and refresh_token."""
        from auth.service import refresh_token_service

        valid_record = _make_refresh_token_record(revoked_at=None)
        mock_usuario = _make_mock_usuario()
        uow = _make_uow(token_record=valid_record, usuario=mock_usuario)
        data = _make_refresh_request()

        with (
            patch("auth.service.create_access_token", return_value="new.access.token"),
            patch("auth.service.create_refresh_token", return_value="new.refresh.token"),
        ):
            result = await refresh_token_service(data, uow)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "new.access.token"
        assert result.refresh_token == "new.refresh.token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_valid_token_revokes_old_record(self):
        """Valid token → old token row gets revoked_at set."""
        from auth.service import refresh_token_service

        valid_record = _make_refresh_token_record(revoked_at=None)
        mock_usuario = _make_mock_usuario()
        uow = _make_uow(token_record=valid_record, usuario=mock_usuario)
        data = _make_refresh_request()

        with (
            patch("auth.service.create_access_token", return_value="new.access.token"),
            patch("auth.service.create_refresh_token", return_value="new.refresh.token"),
        ):
            await refresh_token_service(data, uow)

        # old record should have revoked_at set (not None any more)
        assert valid_record.revoked_at is not None
        uow.refresh_tokens.update.assert_awaited()

    @pytest.mark.asyncio
    async def test_valid_token_creates_new_refresh_token_in_db(self):
        """Valid token → new RefreshToken row is persisted."""
        from auth.service import refresh_token_service

        valid_record = _make_refresh_token_record(revoked_at=None)
        mock_usuario = _make_mock_usuario()
        uow = _make_uow(token_record=valid_record, usuario=mock_usuario)
        data = _make_refresh_request()

        with (
            patch("auth.service.create_access_token", return_value="new.access.token"),
            patch("auth.service.create_refresh_token", return_value="new.refresh.token"),
        ):
            await refresh_token_service(data, uow)

        uow.refresh_tokens.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_valid_token_access_token_has_correct_payload(self):
        """Valid token → create_access_token called with correct sub, email, roles."""
        from auth.service import refresh_token_service

        valid_record = _make_refresh_token_record(revoked_at=None)
        mock_usuario = _make_mock_usuario(id=42, email="alice@example.com")
        uow = _make_uow(token_record=valid_record, usuario=mock_usuario)
        data = _make_refresh_request()

        with (
            patch("auth.service.create_access_token", return_value="new.access.token") as mock_cat,
            patch("auth.service.create_refresh_token", return_value="new.refresh.token"),
        ):
            await refresh_token_service(data, uow)

        called_data = mock_cat.call_args[1]["data"]
        assert called_data["sub"] == "42"
        assert called_data["email"] == "alice@example.com"
        assert "CLIENT" in called_data["roles"]
