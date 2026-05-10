"""
Unit tests for RBAC role management: role_schemas.py, role_service.py, role_router.py.

Uses AsyncMock and MagicMock to isolate all DB and external calls.
Does NOT require a live database connection.

Tests:
  - test_assign_role_success         → 200, role assigned
  - test_assign_same_role_idempotent → 200, no change
  - test_assign_role_user_not_found  → 404
  - test_assign_invalid_role_name    → 422 (Pydantic validation)
  - test_last_admin_protection       → 409
  - test_multiple_admins_can_change_role → 200
  - test_non_admin_forbidden         → 403
  - test_get_user_roles_success      → list of roles
  - test_get_user_roles_empty        → empty list when user not found
  - test_assign_role_nonexistent_role_in_db → 422 (role not in DB)
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_rol(id: int = 1, nombre: str = "CLIENT") -> MagicMock:
    """Build a mock Rol object."""
    rol = MagicMock()
    rol.id = id
    rol.nombre = nombre
    return rol


def _make_mock_usuario(
    *,
    id: int = 1,
    email: str = "user@example.com",
    eliminado_en=None,
    roles: list | None = None,
) -> MagicMock:
    """Build a mock Usuario object with eager-loaded roles."""
    usuario = MagicMock()
    usuario.id = id
    usuario.email = email
    usuario.eliminado_en = eliminado_en
    usuario.roles = roles if roles is not None else [_make_mock_rol(nombre="CLIENT")]
    return usuario


def _make_mock_pivot(usuario_id: int = 1, rol_id: int = 1) -> MagicMock:
    """Build a mock UsuarioRol pivot record."""
    pivot = MagicMock()
    pivot.usuario_id = usuario_id
    pivot.rol_id = rol_id
    return pivot


def _build_execute_result(scalar_one_or_none=None, scalar=None) -> AsyncMock:
    """
    Build a mock SQLAlchemy execute() result.

    - scalar_one_or_none: for single-row queries (Usuario, Rol)
    - scalar: for aggregate queries (COUNT)
    """
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = scalar_one_or_none
    mock_result.scalar.return_value = scalar
    return mock_result


def _make_uow(
    *,
    # Session execute side-effects (called in order or single value)
    session_execute_side_effects: list | None = None,
    session_execute_return_value=None,
    # uow.roles.find_by
    roles_find_by_return=None,
    # uow.usuario_roles.find_all_by
    usuario_roles_find_all_by_return: list | None = None,
    # uow.usuario_roles.find_by
    usuario_roles_find_by_return=None,
) -> MagicMock:
    """Build a mock UnitOfWork with configurable session and repositories."""
    mock_session = AsyncMock()

    if session_execute_side_effects is not None:
        mock_session.execute.side_effect = session_execute_side_effects
    elif session_execute_return_value is not None:
        mock_session.execute.return_value = session_execute_return_value

    mock_session.flush = AsyncMock()
    mock_session.delete = AsyncMock()

    mock_roles_repo = AsyncMock()
    mock_roles_repo.find_by.return_value = roles_find_by_return

    mock_usuario_roles_repo = AsyncMock()
    mock_usuario_roles_repo.find_all_by.return_value = (
        usuario_roles_find_all_by_return if usuario_roles_find_all_by_return is not None else []
    )
    mock_usuario_roles_repo.find_by.return_value = usuario_roles_find_by_return
    mock_usuario_roles_repo.create = AsyncMock()

    uow = MagicMock()
    uow.session = mock_session
    uow.roles = mock_roles_repo
    uow.usuario_roles = mock_usuario_roles_repo

    return uow


# ---------------------------------------------------------------------------
# Schema Tests
# ---------------------------------------------------------------------------

class TestAssignRoleRequest:
    """Tests for AssignRoleRequest Pydantic schema validation."""

    def test_valid_role_client(self):
        """CLIENT is a valid role name."""
        from usuarios.role_schemas import AssignRoleRequest
        req = AssignRoleRequest(rol_nombre="CLIENT")
        assert req.rol_nombre == "CLIENT"

    def test_valid_role_admin(self):
        """ADMIN is a valid role name."""
        from usuarios.role_schemas import AssignRoleRequest
        req = AssignRoleRequest(rol_nombre="ADMIN")
        assert req.rol_nombre == "ADMIN"

    def test_valid_role_stock(self):
        """STOCK is a valid role name."""
        from usuarios.role_schemas import AssignRoleRequest
        req = AssignRoleRequest(rol_nombre="STOCK")
        assert req.rol_nombre == "STOCK"

    def test_valid_role_pedidos(self):
        """PEDIDOS is a valid role name."""
        from usuarios.role_schemas import AssignRoleRequest
        req = AssignRoleRequest(rol_nombre="PEDIDOS")
        assert req.rol_nombre == "PEDIDOS"

    def test_invalid_role_name_raises_validation_error(self):
        """test_assign_invalid_role_name — SUPERUSER is not a valid role → Pydantic ValidationError."""
        from pydantic import ValidationError
        from usuarios.role_schemas import AssignRoleRequest
        with pytest.raises(ValidationError):
            AssignRoleRequest(rol_nombre="SUPERUSER")

    def test_invalid_role_raises_validation_error(self):
        """Empty string is not a valid role."""
        from pydantic import ValidationError
        from usuarios.role_schemas import AssignRoleRequest
        with pytest.raises(ValidationError):
            AssignRoleRequest(rol_nombre="")

    def test_role_name_upcased(self):
        """Role names are uppercased by the validator."""
        from usuarios.role_schemas import AssignRoleRequest
        req = AssignRoleRequest(rol_nombre="admin")
        assert req.rol_nombre == "ADMIN"


# ---------------------------------------------------------------------------
# RoleService — get_user_roles
# ---------------------------------------------------------------------------

class TestGetUserRoles:
    """Tests for RoleService.get_user_roles."""

    @pytest.mark.asyncio
    async def test_get_user_roles_success(self):
        """test_get_user_roles_success — returns UsuarioRol pivot list for user with 1 role."""
        from usuarios.role_service import RoleService

        mock_rol = _make_mock_rol(id=3, nombre="CLIENT")
        mock_usuario = _make_mock_usuario(id=5, roles=[mock_rol])

        execute_result = _build_execute_result(scalar_one_or_none=mock_usuario)
        uow = _make_uow(session_execute_return_value=execute_result)

        result = await RoleService.get_user_roles(uow, user_id=5)

        assert len(result) == 1
        assert result[0].usuario_id == 5
        assert result[0].rol_id == 3

    @pytest.mark.asyncio
    async def test_get_user_roles_empty_when_user_not_found(self):
        """test_get_user_roles_empty — returns [] when user doesn't exist."""
        from usuarios.role_service import RoleService

        execute_result = _build_execute_result(scalar_one_or_none=None)
        uow = _make_uow(session_execute_return_value=execute_result)

        result = await RoleService.get_user_roles(uow, user_id=999)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_roles_multiple_roles(self):
        """User with multiple roles returns multiple UsuarioRol records."""
        from usuarios.role_service import RoleService

        rol_admin = _make_mock_rol(id=1, nombre="ADMIN")
        rol_stock = _make_mock_rol(id=2, nombre="STOCK")
        mock_usuario = _make_mock_usuario(id=7, roles=[rol_admin, rol_stock])

        execute_result = _build_execute_result(scalar_one_or_none=mock_usuario)
        uow = _make_uow(session_execute_return_value=execute_result)

        result = await RoleService.get_user_roles(uow, user_id=7)

        assert len(result) == 2
        rol_ids = {r.rol_id for r in result}
        assert 1 in rol_ids
        assert 2 in rol_ids


# ---------------------------------------------------------------------------
# RoleService — assign_role
# ---------------------------------------------------------------------------

class TestAssignRole:
    """Tests for RoleService.assign_role."""

    @pytest.mark.asyncio
    async def test_assign_role_success(self):
        """test_assign_role_success — ADMIN assigns STOCK role to CLIENT user → HTTP 200."""
        from usuarios.role_service import RoleService

        # User currently has CLIENT role
        mock_client_rol = _make_mock_rol(id=4, nombre="CLIENT")
        mock_usuario = _make_mock_usuario(id=10, roles=[mock_client_rol])

        # First execute → returns user with roles
        user_result = _build_execute_result(scalar_one_or_none=mock_usuario)

        # Target role (STOCK) exists in DB
        mock_stock_rol = _make_mock_rol(id=2, nombre="STOCK")

        # Existing pivot to remove
        existing_pivot = _make_mock_pivot(usuario_id=10, rol_id=4)

        uow = _make_uow(
            session_execute_return_value=user_result,
            roles_find_by_return=mock_stock_rol,
            usuario_roles_find_all_by_return=[existing_pivot],
        )

        result = await RoleService.assign_role(uow, user_id=10, rol_nombre="STOCK")

        assert result.user_id == 10
        assert result.rol_nombre == "STOCK"
        assert "successfully" in result.mensaje.lower() or "stock" in result.mensaje.lower()

        # Verify old pivot was deleted
        uow.session.delete.assert_called_once_with(existing_pivot)
        # Verify new pivot was created
        uow.usuario_roles.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_same_role_idempotent(self):
        """test_assign_same_role_idempotent — assigning same role returns 200 without DB writes."""
        from usuarios.role_service import RoleService

        mock_client_rol = _make_mock_rol(id=4, nombre="CLIENT")
        mock_usuario = _make_mock_usuario(id=11, roles=[mock_client_rol])

        user_result = _build_execute_result(scalar_one_or_none=mock_usuario)
        mock_target_rol = _make_mock_rol(id=4, nombre="CLIENT")

        uow = _make_uow(
            session_execute_return_value=user_result,
            roles_find_by_return=mock_target_rol,
        )

        result = await RoleService.assign_role(uow, user_id=11, rol_nombre="CLIENT")

        assert result.user_id == 11
        assert result.rol_nombre == "CLIENT"
        # Idempotent path — no delete, no create
        uow.session.delete.assert_not_called()
        uow.usuario_roles.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_assign_role_user_not_found(self):
        """test_assign_role_user_not_found — user_id inexistente → HTTP 404."""
        from usuarios.role_service import RoleService

        user_result = _build_execute_result(scalar_one_or_none=None)
        uow = _make_uow(session_execute_return_value=user_result)

        with pytest.raises(HTTPException) as exc_info:
            await RoleService.assign_role(uow, user_id=9999, rol_nombre="STOCK")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_nonexistent_role_in_db(self):
        """test_assign_role_nonexistent_role → role not in DB → HTTP 422."""
        from usuarios.role_service import RoleService

        mock_client_rol = _make_mock_rol(id=4, nombre="CLIENT")
        mock_usuario = _make_mock_usuario(id=12, roles=[mock_client_rol])
        user_result = _build_execute_result(scalar_one_or_none=mock_usuario)

        uow = _make_uow(
            session_execute_return_value=user_result,
            roles_find_by_return=None,  # role not found in DB
        )

        with pytest.raises(HTTPException) as exc_info:
            await RoleService.assign_role(uow, user_id=12, rol_nombre="STOCK")

        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_last_admin_protection(self):
        """test_last_admin_protection — only ADMIN tries to change to STOCK → HTTP 409."""
        from usuarios.role_service import RoleService

        # User is ADMIN
        mock_admin_rol = _make_mock_rol(id=1, nombre="ADMIN")
        mock_usuario = _make_mock_usuario(id=1, roles=[mock_admin_rol])
        user_result = _build_execute_result(scalar_one_or_none=mock_usuario)

        # Target role STOCK exists
        mock_stock_rol = _make_mock_rol(id=2, nombre="STOCK")

        # Admin count = 1 (only one admin)
        admin_count_result = _build_execute_result(scalar=1)

        # DB has ADMIN role
        mock_admin_rol_in_db = _make_mock_rol(id=1, nombre="ADMIN")
        admin_rol_result = _build_execute_result(scalar_one_or_none=mock_admin_rol_in_db)

        # Execute sequence: [user query, ADMIN role query, count query]
        uow = _make_uow(
            session_execute_side_effects=[user_result, admin_rol_result, admin_count_result],
            roles_find_by_return=mock_stock_rol,
        )

        with pytest.raises(HTTPException) as exc_info:
            await RoleService.assign_role(uow, user_id=1, rol_nombre="STOCK")

        assert exc_info.value.status_code == 409
        detail = exc_info.value.detail
        if isinstance(detail, dict):
            assert "last admin" in detail.get("detail", "").lower() or "admin" in str(detail).lower()
        else:
            assert "admin" in str(detail).lower()

    @pytest.mark.asyncio
    async def test_multiple_admins_can_change_role(self):
        """test_multiple_admins_can_change_role — 2 ADMINs, one changes to STOCK → HTTP 200."""
        from usuarios.role_service import RoleService

        # User is ADMIN (admin_id=2)
        mock_admin_rol = _make_mock_rol(id=1, nombre="ADMIN")
        mock_usuario = _make_mock_usuario(id=2, roles=[mock_admin_rol])
        user_result = _build_execute_result(scalar_one_or_none=mock_usuario)

        # Target role STOCK exists
        mock_stock_rol = _make_mock_rol(id=2, nombre="STOCK")

        # Admin count = 2 (two admins, so removal is safe)
        admin_count_result = _build_execute_result(scalar=2)

        # DB has ADMIN role
        mock_admin_rol_in_db = _make_mock_rol(id=1, nombre="ADMIN")
        admin_rol_result = _build_execute_result(scalar_one_or_none=mock_admin_rol_in_db)

        existing_pivot = _make_mock_pivot(usuario_id=2, rol_id=1)

        uow = _make_uow(
            session_execute_side_effects=[user_result, admin_rol_result, admin_count_result],
            roles_find_by_return=mock_stock_rol,
            usuario_roles_find_all_by_return=[existing_pivot],
        )

        result = await RoleService.assign_role(uow, user_id=2, rol_nombre="STOCK")

        assert result.user_id == 2
        assert result.rol_nombre == "STOCK"
        # New pivot created
        uow.usuario_roles.create.assert_called_once()


# ---------------------------------------------------------------------------
# Router / HTTP layer tests (403 non-admin)
# ---------------------------------------------------------------------------

class TestAssignRoleRouter:
    """
    Tests for the role router — HTTP layer.

    test_non_admin_forbidden: Verifies the require_role(["ADMIN"]) dependency
    correctly blocks non-ADMIN users with HTTP 403.
    """

    @pytest.mark.asyncio
    async def test_non_admin_forbidden(self):
        """test_non_admin_forbidden — STOCK user calling endpoint → HTTP 403."""
        from infrastructure.dependencies import require_role
        from core.models import Usuario, Rol

        # Build a STOCK user
        stock_rol = MagicMock(spec=Rol)
        stock_rol.nombre = "STOCK"

        stock_user = MagicMock(spec=Usuario)
        stock_user.id = 50
        stock_user.email = "stock@example.com"
        stock_user.roles = [stock_rol]
        stock_user.eliminado_en = None

        # Invoke the inner dependency returned by require_role(["ADMIN"])
        check_fn = require_role(["ADMIN"])

        # Simulate FastAPI injecting the STOCK user as current_user
        # The inner closure expects current_user as its argument
        import inspect
        sig = inspect.signature(check_fn)
        # The returned function is check_role(current_user=...) — call it directly
        with pytest.raises(HTTPException) as exc_info:
            await check_fn(current_user=stock_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_user_allowed(self):
        """ADMIN user is NOT blocked by require_role(["ADMIN"])."""
        from infrastructure.dependencies import require_role
        from core.models import Usuario, Rol

        admin_rol = MagicMock(spec=Rol)
        admin_rol.nombre = "ADMIN"

        admin_user = MagicMock(spec=Usuario)
        admin_user.id = 1
        admin_user.email = "admin@example.com"
        admin_user.roles = [admin_rol]
        admin_user.eliminado_en = None

        check_fn = require_role(["ADMIN"])

        # Should NOT raise — returns None
        result = await check_fn(current_user=admin_user)
        assert result is None


# ---------------------------------------------------------------------------
# Remove role tests
# ---------------------------------------------------------------------------

class TestRemoveRole:
    """Tests for RoleService.remove_role."""

    @pytest.mark.asyncio
    async def test_remove_role_existing(self):
        """Removing an existing role deletes the pivot record."""
        from usuarios.role_service import RoleService

        mock_rol = _make_mock_rol(id=3, nombre="STOCK")
        mock_pivot = _make_mock_pivot(usuario_id=7, rol_id=3)

        uow = _make_uow(
            roles_find_by_return=mock_rol,
            usuario_roles_find_by_return=mock_pivot,
        )

        await RoleService.remove_role(uow, user_id=7, rol_nombre="STOCK")

        uow.session.delete.assert_called_once_with(mock_pivot)
        uow.session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_role_not_existing_is_idempotent(self):
        """Removing a role the user doesn't have is silent (idempotent)."""
        from usuarios.role_service import RoleService

        mock_rol = _make_mock_rol(id=3, nombre="STOCK")

        uow = _make_uow(
            roles_find_by_return=mock_rol,
            usuario_roles_find_by_return=None,  # pivot not found
        )

        # Should not raise
        await RoleService.remove_role(uow, user_id=7, rol_nombre="STOCK")

        uow.session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_remove_role_nonexistent_role_is_silent(self):
        """Removing a role that doesn't exist in DB is silent."""
        from usuarios.role_service import RoleService

        uow = _make_uow(
            roles_find_by_return=None,  # role not in DB
        )

        await RoleService.remove_role(uow, user_id=7, rol_nombre="GHOST")

        uow.session.delete.assert_not_called()
