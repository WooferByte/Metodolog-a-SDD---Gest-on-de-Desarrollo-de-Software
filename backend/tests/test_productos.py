"""
Unit tests for the productos module.

Strategy:
- Service tests: mock UnitOfWork and ProductoRepository with AsyncMock.
  Tests verify business logic (404 guards, role guards for incluir_eliminados,
  soft-delete) without hitting a real database.
- Router integration tests: use FastAPI TestClient + dependency_overrides to
  verify auth requirements (public GET → 200; POST → 401 without token; POST → 403
  for CLIENT role).
"""

import sys
from decimal import Decimal
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_producto(
    id: int = 1,
    nombre: str = "Producto Test",
    precio_base: Decimal = Decimal("10.00"),
    stock_cantidad: int = 5,
    disponible: bool = True,
) -> MagicMock:
    """Return a MagicMock that quacks like a Producto instance."""
    p = MagicMock()
    p.id = id
    p.nombre = nombre
    p.descripcion = None
    p.precio_base = precio_base
    p.stock_cantidad = stock_cantidad
    p.disponible = disponible
    p.imagen_url = None
    p.creado_en = datetime(2026, 1, 1)
    p.actualizado_en = datetime(2026, 1, 1)
    p.eliminado_en = None
    return p


def _make_uow(repo: MagicMock | None = None) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    The context manager is wired to return the uow itself so that
    ``async with uow:`` works without a real DB transaction.
    """
    uow = MagicMock()
    if repo is None:
        repo = MagicMock()
    uow.productos = repo

    # producto_categorias repo — needed since get_producto_by_id now enriches with categories
    pc_repo = MagicMock()
    pc_repo.get_categorias = AsyncMock(return_value=[])
    uow.producto_categorias = pc_repo

    # producto_ingredientes repo — needed since get_producto_by_id now enriches with ingredients
    pi_repo = MagicMock()
    pi_repo.get_ingredientes = AsyncMock(return_value=[])
    pi_repo.list_active_excluding_alergenos = AsyncMock(return_value=[])
    uow.producto_ingredientes = pi_repo

    # Async context manager wiring
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


def _make_user(roles: list[str]) -> MagicMock:
    """Create a mock Usuario with the given roles."""
    user = MagicMock()
    user.id = 1
    user.activo = True
    user.eliminado_en = None
    user.roles = [MagicMock(nombre=r) for r in roles]
    return user


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestListProductos:
    """list_productos delegates to repository correctly and returns PaginatedProductosResponse."""

    @pytest.mark.asyncio
    async def test_list_productos_returns_active_by_default(self):
        """Service delegates to repo.list_active and returns PaginatedProductosResponse."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        products = [_make_producto(1, "A"), _make_producto(2, "B")]

        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=products)
        repo.count_active = AsyncMock(return_value=2)
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=20, incluir_eliminados=False, page=1, size=20)

        assert isinstance(result, PaginatedProductosResponse)
        assert len(result.items) == 2
        assert result.items[0].id == 1
        assert result.items[1].id == 2
        assert result.total == 2
        assert result.page == 1
        assert result.size == 20
        assert result.pages == 1

    @pytest.mark.asyncio
    async def test_list_productos_con_eliminados_sin_autenticacion_403(self):
        """list_productos with incluir_eliminados=True and no user raises 403."""
        from productos.service import list_productos

        repo = MagicMock()
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await list_productos(uow, incluir_eliminados=True, current_user=None)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_list_productos_con_eliminados_cliente_403(self):
        """list_productos with incluir_eliminados=True and CLIENT role raises 403."""
        from productos.service import list_productos

        repo = MagicMock()
        uow = _make_uow(repo)
        client_user = _make_user(["CLIENT"])

        with pytest.raises(HTTPException) as exc_info:
            await list_productos(uow, incluir_eliminados=True, current_user=client_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_list_productos_con_eliminados_stock_200(self):
        """list_productos with incluir_eliminados=True and STOCK role returns envelope."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        products = [_make_producto(1), _make_producto(2)]
        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=products)
        repo.count_active = AsyncMock(return_value=2)
        uow = _make_uow(repo)
        stock_user = _make_user(["STOCK"])

        result = await list_productos(
            uow, incluir_eliminados=True, current_user=stock_user, skip=0, limit=20, page=1, size=20
        )

        assert isinstance(result, PaginatedProductosResponse)
        assert len(result.items) == 2
        assert result.items[0].id == 1
        assert result.total == 2


class TestGetProductoById:
    """get_producto_by_id raises 404 when repo returns None."""

    @pytest.mark.asyncio
    async def test_get_producto_by_id_not_found(self):
        """Service raises HTTPException 404 when product does not exist."""
        from productos.service import get_producto_by_id

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await get_producto_by_id(uow, 999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_producto_by_id_found(self):
        """Service returns ProductoResponse (enriched with categorias) when repo finds it."""
        from productos.service import get_producto_by_id
        from productos.schemas import ProductoResponse

        product = _make_producto(5, "Found")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=product)
        uow = _make_uow(repo)

        result = await get_producto_by_id(uow, 5)

        # get_producto_by_id now returns ProductoResponse (enriched with categorias=[])
        assert isinstance(result, ProductoResponse)
        assert result.id == 5
        assert result.nombre == "Found"
        assert result.categorias == []


class TestCreateProducto:
    """create_producto calls repo.create and returns the new product."""

    @pytest.mark.asyncio
    async def test_create_producto_success(self):
        """Service calls repo.create and returns the new Producto."""
        from productos.service import create_producto
        from productos.schemas import ProductoCreate

        repo = MagicMock()
        repo.create = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = ProductoCreate(
            nombre="Nuevo Producto",
            precio_base=Decimal("15.99"),
            stock_cantidad=10,
        )
        result = await create_producto(uow, data)

        assert result.nombre == "Nuevo Producto"
        repo.create.assert_awaited_once()


class TestUpdateProducto:
    """update_producto validates existence and applies partial updates."""

    @pytest.mark.asyncio
    async def test_update_producto_not_found(self):
        """Service raises 404 when product does not exist."""
        from productos.service import update_producto
        from productos.schemas import ProductoUpdate

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = ProductoUpdate(nombre="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await update_producto(uow, 99, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_producto_success(self):
        """Valid update returns updated product."""
        from productos.service import update_producto
        from productos.schemas import ProductoUpdate

        product = _make_producto(1, "Old Name")

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=product)
        repo.update = AsyncMock(return_value=product)
        uow = _make_uow(repo)

        data = ProductoUpdate(nombre="New Name")
        result = await update_producto(uow, 1, data)

        assert result is product
        repo.update.assert_awaited_once()


class TestDeleteProducto:
    """delete_producto soft-deletes via repository."""

    @pytest.mark.asyncio
    async def test_delete_producto_not_found(self):
        """Service raises 404 when product does not exist."""
        from productos.service import delete_producto

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        with pytest.raises(HTTPException) as exc_info:
            await delete_producto(uow, 99)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_producto_success(self):
        """Service calls soft_delete when product exists."""
        from productos.service import delete_producto

        product = _make_producto(2, "Free")
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=product)
        repo.soft_delete = AsyncMock()
        uow = _make_uow(repo)

        await delete_producto(uow, 2)

        repo.soft_delete.assert_awaited_once_with(2)


class TestPatchStock:
    """patch_stock updates stock_cantidad only."""

    @pytest.mark.asyncio
    async def test_patch_stock_not_found(self):
        """Service raises 404 when product does not exist."""
        from productos.service import patch_stock
        from productos.schemas import ProductoStockUpdate

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        uow = _make_uow(repo)

        data = ProductoStockUpdate(stock_cantidad=10)

        with pytest.raises(HTTPException) as exc_info:
            await patch_stock(uow, 99, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_stock_success(self):
        """Service updates stock_cantidad and returns updated product."""
        from productos.service import patch_stock
        from productos.schemas import ProductoStockUpdate

        product = _make_producto(1, "Product", stock_cantidad=5)
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=product)
        repo.update = AsyncMock(return_value=product)
        uow = _make_uow(repo)

        data = ProductoStockUpdate(stock_cantidad=20)
        result = await patch_stock(uow, 1, data)

        assert result is product
        assert product.stock_cantidad == 20
        repo.update.assert_awaited_once()


# ---------------------------------------------------------------------------
# Router integration tests (TestClient + dependency_overrides)
# ---------------------------------------------------------------------------


class TestGetProductosPublic:
    """GET /api/v1/productos/ must be accessible without authentication."""

    def test_get_productos_public(self):
        """GET /api/v1/productos/ → 200 without any Authorization header, returns envelope."""
        from main import app
        from infrastructure.uow import get_uow
        from productos.router import get_optional_user
        from productos.schemas import PaginatedProductosResponse

        _envelope = PaginatedProductosResponse(items=[], total=0, page=1, size=20, pages=0)

        async def _fake_uow():
            uow = _make_uow()
            uow.productos.list_active = AsyncMock(return_value=[])
            uow.productos.count_active = AsyncMock(return_value=0)
            return uow

        async def _no_user():
            return None

        app.dependency_overrides[get_uow] = _fake_uow
        app.dependency_overrides[get_optional_user] = _no_user
        try:
            with patch("productos.service.list_productos", new=AsyncMock(return_value=_envelope)):
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/productos/")
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert "page" in data
                assert "size" in data
                assert "pages" in data
        finally:
            app.dependency_overrides.clear()


class TestPostProductoRequiresAuth:
    """POST /api/v1/productos/ must require a valid JWT."""

    def test_post_producto_requires_auth(self):
        """POST /api/v1/productos/ without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/productos/",
                json={
                    "nombre": "Test Producto",
                    "precio_base": "10.00",
                    "stock_cantidad": 5,
                },
            )
        assert response.status_code == 401

    def test_post_producto_requires_stock_role(self):
        """POST /api/v1/productos/ with CLIENT token → 403."""
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
                    "/api/v1/productos/",
                    json={
                        "nombre": "Test Producto",
                        "precio_base": "10.00",
                        "stock_cantidad": 5,
                    },
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_delete_producto_requires_auth(self):
        """DELETE /api/v1/productos/{id} without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.delete("/api/v1/productos/1")
        assert response.status_code == 401

    def test_put_producto_requires_auth(self):
        """PUT /api/v1/productos/{id} without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/api/v1/productos/1",
                json={
                    "nombre": "Updated",
                    "precio_base": "10.00",
                },
            )
        assert response.status_code == 401
