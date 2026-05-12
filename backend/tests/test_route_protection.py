"""
Tests for route protection (RBAC guards) and login activo check.

Strategy:
- Uses FastAPI TestClient (sync) with app.dependency_overrides to mock
  authentication without a live database or real JWT tokens.
- Tests are adapted to the routes that actually exist in the app:
    * /api/v1/auth/login         — POST (public, tests activo check)
    * /api/v1/admin/users/{id}/role — PUT (ADMIN-only via require_role)
- Tests for routers not yet implemented (productos, pedidos, admin/usuarios, etc.)
  are marked with a note that the router does not exist yet and test the
  require_role dependency directly.

IMPORTANT: All tests that need auth dependency overrides target
``infrastructure.dependencies.get_current_user`` — which is what the
existing role_router uses — OR ``core.dependencies.get_current_user``
for new routers added in this change.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from main import app
from core.dependencies import get_current_user, require_role
from infrastructure.dependencies import get_current_user as infra_get_current_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(roles: list[str], activo: bool = True) -> MagicMock:
    """Create a mock Usuario with the given role names."""
    user = MagicMock()
    user.id = 1
    user.activo = activo
    user.eliminado_en = None
    user.roles = [MagicMock(nombre=r) for r in roles]
    return user


def _override_current_user(roles: list[str], activo: bool = True):
    """Override both get_current_user implementations with a mock user."""
    user = _make_user(roles, activo=activo)

    async def _mock_user():
        return user

    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[infra_get_current_user] = _mock_user
    return user


def _clear_overrides():
    """Reset all dependency overrides after a test."""
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 1: Public endpoints don't require auth
# ---------------------------------------------------------------------------


class TestPublicEndpoints:
    """Endpoints with no require_role guard must be reachable without a token."""

    def test_health_endpoint_no_token_returns_200(self):
        """GET /health is public — no token required."""
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/health")
        # Health check must succeed without any auth header
        assert response.status_code == 200

    def test_root_endpoint_no_token_returns_200(self):
        """GET / is public — no token required."""
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Test 2: Protected endpoint without token returns 401
# ---------------------------------------------------------------------------


class TestProtectedEndpointNoToken:
    """Endpoints protected by require_role must return 401 when no token is sent."""

    def test_admin_role_endpoint_no_token_returns_401(self):
        """PUT /api/v1/admin/users/{id}/role without token → 401."""
        _clear_overrides()
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/api/v1/admin/users/1/role",
                json={"rol_nombre": "CLIENT"},
            )
        assert response.status_code == 401

    def teardown_method(self):
        _clear_overrides()


# ---------------------------------------------------------------------------
# Test 3: Wrong role returns 403
# ---------------------------------------------------------------------------


class TestWrongRoleReturns403:
    """User with a role not in the allowed list must get HTTP 403."""

    def test_client_cannot_call_admin_role_endpoint(self):
        """CLIENT token on PUT /api/v1/admin/users/{id}/role → 403."""
        _override_current_user(["CLIENT"])
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/admin/users/1/role",
                    json={"rol_nombre": "CLIENT"},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            _clear_overrides()

    def test_stock_cannot_call_admin_role_endpoint(self):
        """STOCK token on PUT /api/v1/admin/users/{id}/role → 403."""
        _override_current_user(["STOCK"])
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/admin/users/1/role",
                    json={"rol_nombre": "CLIENT"},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            _clear_overrides()

    def test_pedidos_cannot_call_admin_role_endpoint(self):
        """PEDIDOS token on PUT /api/v1/admin/users/{id}/role → 403."""
        _override_current_user(["PEDIDOS"])
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/admin/users/1/role",
                    json={"rol_nombre": "CLIENT"},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# Test 4: Correct role allows access (not 401 / not 403)
# ---------------------------------------------------------------------------


class TestCorrectRoleAllowsAccess:
    """ADMIN user on an ADMIN-guarded endpoint must NOT get 401 or 403."""

    def test_admin_can_call_admin_role_endpoint(self):
        """ADMIN token on PUT /api/v1/admin/users/{id}/role → not 401/403.

        May return 422 (validation) or 404 (user not found) because the UoW
        is still live — we only mock the auth dependency, not the DB.
        The important assertion is that access control passes.
        """
        _override_current_user(["ADMIN"])
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/admin/users/99999/role",
                    json={"rol_nombre": "CLIENT"},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            # Auth passed — any non-auth error code is acceptable
            assert response.status_code not in (401, 403)
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# Test 5: require_role dependency unit tests
# ---------------------------------------------------------------------------


class TestRequireRoleDependencyUnit:
    """Unit tests for require_role factory from core.dependencies.

    These tests invoke the dependency callables directly, without HTTP.
    """

    @pytest.mark.asyncio
    async def test_require_role_passes_for_matching_role(self):
        """require_role passes when user holds one of the allowed roles."""
        from core.dependencies import require_role as core_require_role
        from fastapi import HTTPException

        user = _make_user(["ADMIN"])
        dep = core_require_role(["ADMIN", "STOCK"])
        result = await dep(current_user=user)
        assert result is user  # dependency returns the user

    @pytest.mark.asyncio
    async def test_require_role_raises_403_for_wrong_role(self):
        """require_role raises 403 when user role is not in the allowed list."""
        from core.dependencies import require_role as core_require_role
        from fastapi import HTTPException

        user = _make_user(["CLIENT"])
        dep = core_require_role(["ADMIN", "STOCK"])

        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_role_raises_403_for_empty_roles(self):
        """require_role raises 403 when user has no roles at all."""
        from core.dependencies import require_role as core_require_role
        from fastapi import HTTPException

        user = _make_user([])
        dep = core_require_role(["ADMIN"])

        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_role_multi_role_user_passes(self):
        """User holding STOCK passes require_role(["ADMIN", "STOCK"])."""
        from core.dependencies import require_role as core_require_role

        user = _make_user(["STOCK"])
        dep = core_require_role(["ADMIN", "STOCK"])
        result = await dep(current_user=user)
        assert result is user


# ---------------------------------------------------------------------------
# Test 6: Login activo check
# ---------------------------------------------------------------------------


class TestLoginActivoCheck:
    """login_user must return 403 when usuario.activo == False."""

    @pytest.mark.asyncio
    async def test_inactive_user_login_raises_403(self):
        """Login with activo=False → HTTPException 403 'Cuenta desactivada'."""
        from auth.service import login_user
        from auth.schemas import LoginRequest
        from fastapi import HTTPException

        # Build a mock usuario with activo=False
        mock_usuario = MagicMock()
        mock_usuario.id = 1
        mock_usuario.email = "inactive@example.com"
        mock_usuario.hashed_password = "hashed_pw"
        mock_usuario.nombre = "Inactive"
        mock_usuario.apellido = None
        mock_usuario.activo = False
        mock_rol = MagicMock()
        mock_rol.nombre = "CLIENT"
        mock_usuario.roles = [mock_rol]

        # Build UoW mock — session.execute returns the inactive user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_usuario

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        uow = MagicMock()
        uow.session = mock_session
        uow.refresh_tokens = AsyncMock()

        data = LoginRequest(email="inactive@example.com", password="AnyPass1")

        with patch("auth.service.verify_password", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                await login_user(data, uow)

        assert exc_info.value.status_code == 403
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert "desactivada" in detail.get("detail", "").lower()
        else:
            assert "desactivada" in str(detail).lower()

    @pytest.mark.asyncio
    async def test_active_user_login_succeeds(self):
        """Login with activo=True returns TokenResponse (no 403)."""
        from auth.service import login_user
        from auth.schemas import LoginRequest, TokenResponse
        from fastapi import HTTPException

        mock_rol = MagicMock()
        mock_rol.nombre = "CLIENT"

        mock_usuario = MagicMock()
        mock_usuario.id = 2
        mock_usuario.email = "active@example.com"
        mock_usuario.hashed_password = "hashed_pw"
        mock_usuario.nombre = "Active"
        mock_usuario.apellido = None
        mock_usuario.activo = True  # ← active
        mock_usuario.roles = [mock_rol]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_usuario

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        uow = MagicMock()
        uow.session = mock_session
        uow.refresh_tokens = AsyncMock()
        uow.refresh_tokens.create = AsyncMock(return_value=MagicMock())

        data = LoginRequest(email="active@example.com", password="AnyPass1")

        with (
            patch("auth.service.verify_password", return_value=True),
            patch("auth.service.create_access_token", return_value="access.token"),
            patch("auth.service.create_refresh_token", return_value="refresh.token"),
            patch("auth.service.UsuarioResponse.model_validate", return_value=MagicMock()),
        ):
            result = await login_user(data, uow)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access.token"


# ---------------------------------------------------------------------------
# Test 7 (note): Routers not yet implemented
# ---------------------------------------------------------------------------
#
# The following routers are not yet implemented in this codebase:
#   - backend/productos/router.py      (BLOQUE 3)
#   - backend/categorias/router.py     (BLOQUE 3)
#   - backend/ingredientes/router.py   (BLOQUE 3)
#   - backend/pedidos/router.py        (BLOQUE 4)
#   - backend/usuarios/router.py       (perfil, cambiar-password)
#   - backend/direcciones/router.py
#   - backend/admin/router.py          (usuarios, metricas, configuracion)
#
# When those routers are implemented they MUST use:
#   from core.dependencies import require_role
#
# Guard mapping (to implement at that point):
#   GET /api/v1/productos             → public
#   POST/PUT/DELETE /api/v1/productos → require_role(["ADMIN", "STOCK"])
#   GET/PUT /api/v1/perfil            → require_role(["CLIENT"])
#   POST /api/v1/perfil/cambiar-password → require_role(["CLIENT"])
#   * /api/v1/direcciones/*           → require_role(["CLIENT"])
#   POST/GET /api/v1/pedidos          → require_role(["CLIENT"])
#   PATCH /api/v1/pedidos/{id}/avanzar → require_role(["ADMIN", "PEDIDOS"])
#   GET /api/v1/admin/usuarios        → require_role(["ADMIN"])
#   GET /api/v1/admin/pedidos         → require_role(["ADMIN", "PEDIDOS"])
#   /api/v1/admin/metricas/*          → require_role(["ADMIN"])
#   /api/v1/admin/configuracion       → require_role(["ADMIN"])
