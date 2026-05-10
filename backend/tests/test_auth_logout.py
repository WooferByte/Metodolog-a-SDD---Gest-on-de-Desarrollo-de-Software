"""
Unit tests for auth logout: service.py logout_user function.

Uses AsyncMock and MagicMock to isolate all DB and external calls.
Does NOT require a live database connection.

Security scenarios tested:
- Valid active token → revokes token (revoked_at set), returns None → router sends 204
- Already-revoked token → idempotent, returns None → router sends 204
- Unknown token → 401 "Invalid refresh token"
- logout_user does NOT affect other sessions (does not revoke sibling tokens)
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

from fastapi import HTTPException

from auth.schemas import RefreshRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_refresh_token_record(
    *,
    id: int = 10,
    usuario_id: int = 1,
    token: str = "valid.refresh.token",
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> MagicMock:
    """Build a mock RefreshToken DB record."""
    mock = MagicMock()
    mock.id = id
    mock.usuario_id = usuario_id
    mock.token = token
    mock.expires_at = expires_at or (datetime.utcnow() + timedelta(days=7))
    mock.revoked_at = revoked_at
    return mock


def _make_uow(
    *,
    token_record: MagicMock | None = None,
) -> MagicMock:
    """Build a mock UnitOfWork with a refresh_tokens repository."""
    mock_refresh_repo = AsyncMock()
    mock_refresh_repo.find_by.return_value = token_record
    mock_refresh_repo.update.return_value = token_record

    uow = MagicMock()
    uow.refresh_tokens = mock_refresh_repo
    return uow


def _make_logout_request(refresh_token: str = "valid.refresh.token") -> RefreshRequest:
    return RefreshRequest(refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestLogoutUserService:
    """Tests for auth.service.logout_user."""

    @pytest.mark.asyncio
    async def test_valid_active_token_revokes_it(self):
        """
        POST /auth/logout with a valid active token →
        revoked_at is set on the record and update() is called.
        """
        from auth.service import logout_user

        active_record = _make_refresh_token_record(revoked_at=None)
        uow = _make_uow(token_record=active_record)
        data = _make_logout_request()

        result = await logout_user(data, uow)

        # Return value is None (router returns 204)
        assert result is None

        # revoked_at must be set
        assert active_record.revoked_at is not None
        assert isinstance(active_record.revoked_at, datetime)

        # update() must have been called once with the record
        uow.refresh_tokens.update.assert_awaited_once_with(active_record)

    @pytest.mark.asyncio
    async def test_valid_active_token_returns_none(self):
        """logout_user returns None so the router can return 204 No Content."""
        from auth.service import logout_user

        active_record = _make_refresh_token_record(revoked_at=None)
        uow = _make_uow(token_record=active_record)
        data = _make_logout_request()

        result = await logout_user(data, uow)
        assert result is None

    @pytest.mark.asyncio
    async def test_already_revoked_token_is_idempotent(self):
        """
        POST /auth/logout with a previously-revoked token →
        returns None (204), does NOT call update() again.
        """
        from auth.service import logout_user

        revoked_record = _make_refresh_token_record(
            revoked_at=datetime.utcnow() - timedelta(hours=1)
        )
        uow = _make_uow(token_record=revoked_record)
        data = _make_logout_request()

        result = await logout_user(data, uow)

        # Still returns None → router sends 204
        assert result is None

        # update() must NOT have been called (already revoked, idempotent)
        uow.refresh_tokens.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unknown_token_raises_401(self):
        """
        POST /auth/logout with a token not in DB →
        raises HTTPException 401 "Invalid refresh token".
        """
        from auth.service import logout_user

        uow = _make_uow(token_record=None)  # token not found
        data = _make_logout_request("totally.unknown.token")

        with pytest.raises(HTTPException) as exc_info:
            await logout_user(data, uow)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_logout_does_not_affect_other_sessions(self):
        """
        logout_user only revokes the given token —
        it does NOT call find_all_by or bulk-revoke sibling tokens.
        This ensures single-session logout only.
        """
        from auth.service import logout_user

        active_record = _make_refresh_token_record(revoked_at=None)
        uow = _make_uow(token_record=active_record)
        data = _make_logout_request()

        await logout_user(data, uow)

        # find_all_by (bulk lookup) must NOT have been called
        uow.refresh_tokens.find_all_by.assert_not_called()

        # update() called exactly once (for the target token only)
        assert uow.refresh_tokens.update.await_count == 1

    @pytest.mark.asyncio
    async def test_revoked_at_is_set_to_approximately_now(self):
        """revoked_at timestamp is approximately UTC now (within 5 seconds)."""
        from auth.service import logout_user

        active_record = _make_refresh_token_record(revoked_at=None)
        uow = _make_uow(token_record=active_record)
        data = _make_logout_request()

        before = datetime.utcnow()
        await logout_user(data, uow)
        after = datetime.utcnow()

        assert before <= active_record.revoked_at <= after
