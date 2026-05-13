"""
Unit tests for the categorias module.

Strategy:
- Service tests: mock UnitOfWork and CategoriaRepository with AsyncMock.
  Tests verify business logic (404 guards, cycle detection, product guards,
  IntegrityError → 409) without hitting a real database.
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


def _make_categoria(
    id: int = 1,
    nombre: str = "Test",
    padre_id: int | None = None,
) -> MagicMock:
    """Return a MagicMock that quacks like a Categoria instance."""
    cat = MagicMock()
    cat.id = id
    cat.nombre = nombre
    cat.descripcion = None
    cat.padre_id = padre_id
    cat.creado_en = datetime(2026, 1, 1)
    cat.actualizado_en = datetime(2026, 1, 1)
    cat.eliminado_en = None
    return cat


def _make_uow(repo: MagicMock | None = None) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    The context manager is wired to return the uow itself so that
    ``async with uow:`` works without a real DB transaction.
    """
    uow = MagicMock()
    if repo is None:
        repo = MagicMock()
    uow.categorias = repo

    # Async context manager wiring
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestListCategorias:
    """list_categorias returns whatever the repository returns."""

    @pytest.mark.asyncio
    async def test_list_categorias_returns_active_only(self):
        """Service delegates to repository and returns its result unchanged."""
        from categorias.service import list_categorias

        cats = [_make_categoria(1, "A"), _make_categoria(2, "B")]

        repo = MagicMock()
        repo.list_all = AsyncMock(return_value=cats)
        uow = _make_uow(repo)

        result = await list_categorias(uow, skip=0, limit=100)

        assert result == cats
        repo.list_all.assert_awaited_once_with(skip=0, limit=100)


class TestGetCategoriaById:
    """get_categoria_by_id raises 404 when repo returns None."""

    @pytest.mark.asyncio
    async def test_get_categoria_by_id_not_found(self):
        """Service raises HTTPException 404 when category does not exist."""
        from categorias.service import get_categoria_by_id

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await get_categoria_by_id(uow, 999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_categoria_by_id_found(self):
        """Service returns category when repo finds it."""
        from categorias.service import get_categoria_by_id

        cat = _make_categoria(5, "Found")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=cat)
        uow = _make_uow(repo)

        result = await get_categoria_by_id(uow, 5)

        assert result is cat


class TestCreateCategoria:
    """create_categoria validates parent and handles IntegrityError."""

    @pytest.mark.asyncio
    async def test_create_categoria_success(self):
        """Service calls repo.create and returns the new category."""
        from categorias.service import create_categoria
        from categorias.schemas import CategoriaCreate

        # repo.create mutates the entity in-place (no return value used in service)
        repo = MagicMock()
        repo.create = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = CategoriaCreate(nombre="New Category")
        result = await create_categoria(uow, data)

        # Result is the Categoria instance built from data
        assert result.nombre == "New Category"
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_categoria_with_valid_parent(self):
        """Service verifies parent exists before creating child."""
        from categorias.service import create_categoria
        from categorias.schemas import CategoriaCreate

        parent = _make_categoria(1, "Parent")

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=parent)
        repo.create = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = CategoriaCreate(nombre="Child", padre_id=1)
        result = await create_categoria(uow, data)

        assert result.nombre == "Child"
        assert result.padre_id == 1
        repo.get_by_id.assert_awaited_with(1)

    @pytest.mark.asyncio
    async def test_create_categoria_parent_not_found(self):
        """Service raises 404 if padre_id does not exist."""
        from categorias.service import create_categoria
        from categorias.schemas import CategoriaCreate

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = CategoriaCreate(nombre="Child", padre_id=99)

        with pytest.raises(HTTPException) as exc_info:
            await create_categoria(uow, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_categoria_duplicate_name(self):
        """Service converts IntegrityError → HTTPException 409."""
        from categorias.service import create_categoria
        from categorias.schemas import CategoriaCreate

        repo = MagicMock()
        repo.create = AsyncMock(
            side_effect=IntegrityError("UNIQUE", {}, Exception("unique"))
        )
        uow = _make_uow(repo)

        data = CategoriaCreate(nombre="Duplicate")

        with pytest.raises(HTTPException) as exc_info:
            await create_categoria(uow, data)

        assert exc_info.value.status_code == 409


class TestUpdateCategoria:
    """update_categoria validates cycles, parent existence, and IntegrityError."""

    @pytest.mark.asyncio
    async def test_update_categoria_cycle_detection(self):
        """
        A→B→C structure: updating A's padre_id to C must raise 400.

        Category A (id=1) already has child B (id=2) which has child C (id=3).
        Setting padre_id=3 on category A would close the cycle A→B→C→A.
        """
        from categorias.service import update_categoria
        from categorias.schemas import CategoriaUpdate

        # A=1 (top), B=2 (child of A), C=3 (child of B)
        cat_a = _make_categoria(1, "A", padre_id=None)
        cat_b = _make_categoria(2, "B", padre_id=1)
        cat_c = _make_categoria(3, "C", padre_id=2)

        # get_by_id:
        #   called with 1 → cat_a (current category being updated)
        #   called with 3 → cat_c (proposed padre_id)
        #   called with 2 → cat_b (ancestor of C)
        #   called with 1 → cat_a (ancestor of B) → cycle found
        async def _get_by_id(id: int):
            return {1: cat_a, 2: cat_b, 3: cat_c}.get(id)

        repo = MagicMock()
        repo.get_by_id = AsyncMock(side_effect=_get_by_id)
        uow = _make_uow(repo)

        data = CategoriaUpdate(padre_id=3)  # would close cycle A→B→C→A

        with pytest.raises(HTTPException) as exc_info:
            await update_categoria(uow, 1, data)

        assert exc_info.value.status_code == 400
        detail_str = str(exc_info.value.detail)
        assert "cycle" in detail_str.lower()

    @pytest.mark.asyncio
    async def test_update_categoria_self_cycle(self):
        """Setting padre_id == categoria_id must raise 400 immediately."""
        from categorias.service import update_categoria
        from categorias.schemas import CategoriaUpdate

        cat = _make_categoria(5, "Self")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=cat)
        uow = _make_uow(repo)

        data = CategoriaUpdate(padre_id=5)  # self-reference

        with pytest.raises(HTTPException) as exc_info:
            await update_categoria(uow, 5, data)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_categoria_success(self):
        """Valid update (no cycle, no duplicate) returns updated category."""
        from categorias.service import update_categoria
        from categorias.schemas import CategoriaUpdate

        cat = _make_categoria(1, "Old Name")
        cat.nombre = "Old Name"

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=cat)
        repo.update = AsyncMock(return_value=cat)
        uow = _make_uow(repo)

        data = CategoriaUpdate(nombre="New Name")
        result = await update_categoria(uow, 1, data)

        assert result is cat
        repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_categoria_duplicate_name(self):
        """IntegrityError during update → HTTPException 409."""
        from categorias.service import update_categoria
        from categorias.schemas import CategoriaUpdate

        cat = _make_categoria(1, "Original")

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=cat)
        repo.update = AsyncMock(
            side_effect=IntegrityError("UNIQUE", {}, Exception("unique"))
        )
        uow = _make_uow(repo)

        data = CategoriaUpdate(nombre="Taken")

        with pytest.raises(HTTPException) as exc_info:
            await update_categoria(uow, 1, data)

        assert exc_info.value.status_code == 409


class TestDeleteCategoria:
    """delete_categoria is guarded by active-products check."""

    @pytest.mark.asyncio
    async def test_delete_categoria_blocked_by_products(self):
        """Service raises 409 when category has active products."""
        from categorias.service import delete_categoria

        cat = _make_categoria(1, "Busy")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=cat)
        repo.has_active_products = AsyncMock(return_value=True)
        repo.soft_delete = AsyncMock()
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await delete_categoria(uow, 1)

        assert exc_info.value.status_code == 409
        repo.soft_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_categoria_success(self):
        """Service calls soft_delete when no active products."""
        from categorias.service import delete_categoria

        cat = _make_categoria(2, "Free")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=cat)
        repo.has_active_products = AsyncMock(return_value=False)
        repo.soft_delete = AsyncMock()
        uow = _make_uow(repo)

        await delete_categoria(uow, 2)

        repo.soft_delete.assert_awaited_once_with(2)

    @pytest.mark.asyncio
    async def test_delete_categoria_not_found(self):
        """Service raises 404 when category does not exist."""
        from categorias.service import delete_categoria

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await delete_categoria(uow, 99)

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


class TestGetCategoriasPublic:
    """GET /api/v1/categorias must be accessible without authentication."""

    def test_get_categorias_public(self):
        """GET /api/v1/categorias → 200 without any Authorization header."""
        from main import app
        from infrastructure.uow import get_uow
        from categorias.service import list_categorias

        async def _mock_uow():
            uow = _make_uow()
            uow.categorias.list_all = AsyncMock(return_value=[])
            return uow

        with patch("categorias.service.list_categorias", new=AsyncMock(return_value=[])):
            # Override get_uow to avoid DB
            async def _fake_uow():
                uow = _make_uow()
                uow.categorias.list_all = AsyncMock(return_value=[])
                return uow

            app.dependency_overrides[get_uow] = _fake_uow
            try:
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/categorias/")
                assert response.status_code == 200
            finally:
                app.dependency_overrides.clear()

    def test_get_tree_public(self):
        """GET /api/v1/categorias/tree → 200 without Authorization."""
        from main import app
        from infrastructure.uow import get_uow

        async def _fake_uow():
            uow = _make_uow()
            uow.categorias.get_tree = AsyncMock(return_value=[])
            return uow

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with patch("categorias.service.get_tree", new=AsyncMock(return_value=[])):
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/categorias/tree")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestPostCategoriaRequiresAuth:
    """POST /api/v1/categorias must require a valid JWT."""

    def test_post_categoria_requires_auth(self):
        """POST /api/v1/categorias without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/categorias/",
                json={"nombre": "Test Category"},
            )
        assert response.status_code == 401

    def test_post_categoria_requires_stock_role(self):
        """POST /api/v1/categorias with CLIENT token → 403."""
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
                    "/api/v1/categorias/",
                    json={"nombre": "Test Category"},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_delete_categoria_requires_auth(self):
        """DELETE /api/v1/categorias/{id} without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.delete("/api/v1/categorias/1")
        assert response.status_code == 401

    def test_put_categoria_requires_auth(self):
        """PUT /api/v1/categorias/{id} without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/api/v1/categorias/1",
                json={"nombre": "Updated"},
            )
        assert response.status_code == 401
