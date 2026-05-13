"""
Unit tests for the ingredientes module.

Strategy:
- Service tests: mock UnitOfWork and IngredienteRepository with AsyncMock.
  Tests verify business logic (404 guards, UNIQUE → 409, active-products guard on delete)
  without hitting a real database.
- Router integration tests: use FastAPI TestClient + dependency_overrides to
  verify auth requirements (public endpoints return 200; protected endpoints
  return 401 without token and 403 for CLIENT role).
"""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_ingrediente(
    id: int = 1,
    nombre: str = "Tomate",
    es_alergeno: bool = False,
) -> MagicMock:
    """Return a MagicMock that quacks like an Ingrediente instance."""
    ing = MagicMock()
    ing.id = id
    ing.nombre = nombre
    ing.es_alergeno = es_alergeno
    ing.creado_en = datetime(2026, 1, 1)
    ing.eliminado_en = None
    return ing


def _make_uow(repo: MagicMock | None = None) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    The context manager is wired to return the uow itself so that
    ``async with uow:`` works without a real DB transaction.
    """
    uow = MagicMock()
    if repo is None:
        repo = MagicMock()
    uow.ingredientes = repo

    # Async context manager wiring
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestListIngredientes:
    """list_ingredientes returns whatever the repository returns."""

    @pytest.mark.asyncio
    async def test_list_ingredientes_no_filter(self):
        """Service delegates to list_all when es_alergeno is None."""
        from ingredientes.service import list_ingredientes

        ings = [_make_ingrediente(1, "Tomate"), _make_ingrediente(2, "Cebolla")]

        repo = MagicMock()
        repo.list_all = AsyncMock(return_value=ings)
        uow = _make_uow(repo)

        result = await list_ingredientes(uow, skip=0, limit=100, es_alergeno=None)

        assert result == ings
        repo.list_all.assert_awaited_once_with(skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_list_ingredientes_filter_alergenos(self):
        """Service delegates to list_by_alergeno when es_alergeno is True."""
        from ingredientes.service import list_ingredientes

        ings = [_make_ingrediente(3, "Maní", es_alergeno=True)]

        repo = MagicMock()
        repo.list_by_alergeno = AsyncMock(return_value=ings)
        uow = _make_uow(repo)

        result = await list_ingredientes(uow, skip=0, limit=100, es_alergeno=True)

        assert result == ings
        repo.list_by_alergeno.assert_awaited_once_with(es_alergeno=True, skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_list_ingredientes_filter_no_alergenos(self):
        """Service delegates to list_by_alergeno when es_alergeno is False."""
        from ingredientes.service import list_ingredientes

        ings = [_make_ingrediente(1, "Tomate", es_alergeno=False)]

        repo = MagicMock()
        repo.list_by_alergeno = AsyncMock(return_value=ings)
        uow = _make_uow(repo)

        result = await list_ingredientes(uow, skip=0, limit=100, es_alergeno=False)

        assert result == ings
        repo.list_by_alergeno.assert_awaited_once_with(es_alergeno=False, skip=0, limit=100)


class TestGetIngredienteById:
    """get_ingrediente_by_id raises 404 when repo returns None."""

    @pytest.mark.asyncio
    async def test_get_ingrediente_by_id_not_found(self):
        """Service raises HTTPException 404 when ingredient does not exist."""
        from ingredientes.service import get_ingrediente_by_id

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await get_ingrediente_by_id(uow, 999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_ingrediente_by_id_found(self):
        """Service returns ingredient when repo finds it."""
        from ingredientes.service import get_ingrediente_by_id

        ing = _make_ingrediente(5, "Orégano")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=ing)
        uow = _make_uow(repo)

        result = await get_ingrediente_by_id(uow, 5)

        assert result is ing


class TestCreateIngrediente:
    """create_ingrediente validates and handles IntegrityError."""

    @pytest.mark.asyncio
    async def test_create_ingrediente_success(self):
        """Service calls repo.create and returns the new ingredient."""
        from ingredientes.service import create_ingrediente
        from ingredientes.schemas import IngredienteCreate

        repo = MagicMock()
        repo.create = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = IngredienteCreate(nombre="Albahaca", es_alergeno=False)
        result = await create_ingrediente(uow, data)

        assert result.nombre == "Albahaca"
        assert result.es_alergeno is False
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_ingrediente_duplicate_name(self):
        """Service converts IntegrityError → HTTPException 409."""
        from ingredientes.service import create_ingrediente
        from ingredientes.schemas import IngredienteCreate

        repo = MagicMock()
        repo.create = AsyncMock(
            side_effect=IntegrityError("UNIQUE", {}, Exception("unique"))
        )
        uow = _make_uow(repo)

        data = IngredienteCreate(nombre="Duplicate", es_alergeno=False)

        with pytest.raises(HTTPException) as exc_info:
            await create_ingrediente(uow, data)

        assert exc_info.value.status_code == 409


class TestUpdateIngrediente:
    """update_ingrediente validates existence and handles IntegrityError."""

    @pytest.mark.asyncio
    async def test_update_ingrediente_success(self):
        """Valid update returns updated ingredient."""
        from ingredientes.service import update_ingrediente
        from ingredientes.schemas import IngredienteUpdate

        ing = _make_ingrediente(1, "OldName")

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=ing)
        repo.update = AsyncMock(return_value=ing)
        uow = _make_uow(repo)

        data = IngredienteUpdate(nombre="NewName")
        result = await update_ingrediente(uow, 1, data)

        assert result is ing
        repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_ingrediente_not_found(self):
        """Service raises 404 for ID that does not exist."""
        from ingredientes.service import update_ingrediente
        from ingredientes.schemas import IngredienteUpdate

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = IngredienteUpdate(nombre="Something")

        with pytest.raises(HTTPException) as exc_info:
            await update_ingrediente(uow, 999, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_ingrediente_duplicate_name(self):
        """IntegrityError during update → HTTPException 409."""
        from ingredientes.service import update_ingrediente
        from ingredientes.schemas import IngredienteUpdate

        ing = _make_ingrediente(1, "Original")

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=ing)
        repo.update = AsyncMock(
            side_effect=IntegrityError("UNIQUE", {}, Exception("unique"))
        )
        uow = _make_uow(repo)

        data = IngredienteUpdate(nombre="Taken")

        with pytest.raises(HTTPException) as exc_info:
            await update_ingrediente(uow, 1, data)

        assert exc_info.value.status_code == 409


class TestDeleteIngrediente:
    """delete_ingrediente is guarded by active-products check."""

    @pytest.mark.asyncio
    async def test_delete_ingrediente_blocked_by_products(self):
        """Service raises 409 when ingredient has active products."""
        from ingredientes.service import delete_ingrediente

        ing = _make_ingrediente(1, "Busy")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=ing)
        repo.has_active_products = AsyncMock(return_value=True)
        repo.soft_delete = AsyncMock()
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await delete_ingrediente(uow, 1)

        assert exc_info.value.status_code == 409
        repo.soft_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_ingrediente_success(self):
        """Service calls soft_delete when no active products."""
        from ingredientes.service import delete_ingrediente

        ing = _make_ingrediente(2, "Free")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=ing)
        repo.has_active_products = AsyncMock(return_value=False)
        repo.soft_delete = AsyncMock()
        uow = _make_uow(repo)

        await delete_ingrediente(uow, 2)

        repo.soft_delete.assert_awaited_once_with(2)

    @pytest.mark.asyncio
    async def test_delete_ingrediente_not_found(self):
        """Service raises 404 when ingredient does not exist."""
        from ingredientes.service import delete_ingrediente

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await delete_ingrediente(uow, 99)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Router integration tests (TestClient + dependency_overrides)
# ---------------------------------------------------------------------------


def _make_user(roles: list[str]) -> MagicMock:
    """Create a mock Usuario with the given roles."""
    user = MagicMock()
    user.id = 1
    user.activo = True
    user.eliminado_en = None
    user.roles = [MagicMock(nombre=r) for r in roles]
    return user


class TestGetIngredientesPublic:
    """GET /api/v1/ingredientes must be accessible without authentication."""

    def test_get_ingredientes_public(self):
        """GET /api/v1/ingredientes/ → 200 without any Authorization header."""
        from main import app
        from infrastructure.uow import get_uow

        async def _fake_uow():
            uow = _make_uow()
            uow.ingredientes.list_all = AsyncMock(return_value=[])
            return uow

        with patch("ingredientes.service.list_ingredientes", new=AsyncMock(return_value=[])):
            app.dependency_overrides[get_uow] = _fake_uow
            try:
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/ingredientes/")
                assert response.status_code == 200
            finally:
                app.dependency_overrides.clear()


class TestPostIngredienteRequiresAuth:
    """POST /api/v1/ingredientes must require a valid JWT."""

    def test_post_ingrediente_without_token_returns_401(self):
        """POST /api/v1/ingredientes/ without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/ingredientes/",
                json={"nombre": "Test Ingrediente", "es_alergeno": False},
            )
        assert response.status_code == 401

    def test_post_ingrediente_with_client_role_returns_403(self):
        """POST /api/v1/ingredientes/ with CLIENT token → 403."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user

        client_user = _make_user(["CLIENT"])

        async def _mock_user():
            return client_user

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/ingredientes/",
                    json={"nombre": "Test Ingrediente", "es_alergeno": False},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


class TestDeleteIngredienteRequiresAuth:
    """DELETE /api/v1/ingredientes/{id} must require a valid JWT."""

    def test_delete_ingrediente_without_token_returns_401(self):
        """DELETE /api/v1/ingredientes/{id} without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.delete("/api/v1/ingredientes/1")
        assert response.status_code == 401


class TestPutIngredienteRequiresAuth:
    """PUT /api/v1/ingredientes/{id} must require a valid JWT."""

    def test_put_ingrediente_without_token_returns_401(self):
        """PUT /api/v1/ingredientes/{id} without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/api/v1/ingredientes/1",
                json={"nombre": "Updated"},
            )
        assert response.status_code == 401
