"""
Unit + integration tests for products-categories-association change.

Strategy:
- Service tests: mock UnitOfWork with AsyncMock — no real DB.
- Router integration tests: FastAPI TestClient + dependency_overrides.

Coverage: list_categorias_producto, set_categorias_producto,
          remove_categoria_producto, and the enriched get_producto_by_id.
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_producto(id: int = 1, nombre: str = "Producto Test") -> MagicMock:
    """Return a MagicMock that quacks like a Producto instance."""
    p = MagicMock()
    p.id = id
    p.nombre = nombre
    p.descripcion = None
    p.precio_base = Decimal("10.00")
    p.stock_cantidad = 5
    p.disponible = True
    p.imagen_url = None
    p.creado_en = datetime(2026, 1, 1)
    p.actualizado_en = datetime(2026, 1, 1)
    p.eliminado_en = None
    return p


def _make_categoria(id: int = 1, nombre: str = "Cat Test", padre_id=None) -> MagicMock:
    """Return a MagicMock that quacks like a Categoria instance."""
    c = MagicMock()
    c.id = id
    c.nombre = nombre
    c.padre_id = padre_id
    c.eliminado_en = None
    return c


def _make_pivot(producto_id: int = 1, categoria_id: int = 1) -> MagicMock:
    """Return a MagicMock for a ProductoCategoria pivot row."""
    p = MagicMock()
    p.producto_id = producto_id
    p.categoria_id = categoria_id
    return p


def _make_uow(
    producto=None,
    categorias_list=None,
    categoria_obj=None,
    pivot=None,
) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    Wires:
    - uow.productos.get_by_id → producto (or None)
    - uow.producto_categorias.get_categorias → categorias_list (or [])
    - uow.categorias.get_by_id → categoria_obj (or a real mock Categoria)
    - uow.producto_categorias.get_association → pivot (or None)
    - uow.producto_categorias.set_categorias → AsyncMock (no-op)
    - uow.producto_categorias.remove_categoria → AsyncMock (no-op)
    - uow.producto_ingredientes.get_ingredientes → AsyncMock (returns [])
    """
    uow = MagicMock()

    # productos repo
    productos_repo = MagicMock()
    productos_repo.get_by_id = AsyncMock(return_value=producto)
    uow.productos = productos_repo

    # producto_categorias repo
    pc_repo = MagicMock()
    pc_repo.get_categorias = AsyncMock(return_value=categorias_list or [])
    pc_repo.set_categorias = AsyncMock(return_value=None)
    pc_repo.get_association = AsyncMock(return_value=pivot)
    pc_repo.remove_categoria = AsyncMock(return_value=None)
    uow.producto_categorias = pc_repo

    # categorias repo
    cat_repo = MagicMock()
    cat_repo.get_by_id = AsyncMock(return_value=categoria_obj)
    uow.categorias = cat_repo

    # producto_ingredientes repo — needed since get_producto_by_id now enriches with ingredients
    pi_repo = MagicMock()
    pi_repo.get_ingredientes = AsyncMock(return_value=[])
    uow.producto_ingredientes = pi_repo

    # Async context manager
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
# Service tests — list_categorias_producto
# ---------------------------------------------------------------------------


class TestListCategoriasProducto:
    """list_categorias_producto service function tests."""

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Raises 404 when product does not exist."""
        from productos.service import list_categorias_producto

        uow = _make_uow(producto=None)

        with pytest.raises(HTTPException) as exc_info:
            await list_categorias_producto(uow, 999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_producto_sin_categorias_retorna_lista_vacia(self):
        """Returns empty list when product has no categories."""
        from productos.service import list_categorias_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, categorias_list=[])

        result = await list_categorias_producto(uow, 1)

        assert result == []

    @pytest.mark.asyncio
    async def test_producto_con_categorias_retorna_lista(self):
        """Returns compact list of categories when associations exist."""
        from productos.service import list_categorias_producto

        producto = _make_producto(1)
        cats = [_make_categoria(1, "Cat A"), _make_categoria(2, "Cat B", padre_id=1)]
        uow = _make_uow(producto=producto, categorias_list=cats)

        result = await list_categorias_producto(uow, 1)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].nombre == "Cat A"
        assert result[0].padre_id is None
        assert result[1].id == 2
        assert result[1].padre_id == 1


# ---------------------------------------------------------------------------
# Service tests — set_categorias_producto
# ---------------------------------------------------------------------------


class TestSetCategoriasProducto:
    """set_categorias_producto service function tests."""

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Raises 404 when product does not exist."""
        from productos.schemas import ProductoCategoriaSetRequest
        from productos.service import set_categorias_producto

        uow = _make_uow(producto=None)
        data = ProductoCategoriaSetRequest(categoria_ids=[1])

        with pytest.raises(HTTPException) as exc_info:
            await set_categorias_producto(uow, 999, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_categoria_inexistente_404(self):
        """Raises 404 if any categoria_id does not exist."""
        from productos.schemas import ProductoCategoriaSetRequest
        from productos.service import set_categorias_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, categoria_obj=None)
        data = ProductoCategoriaSetRequest(categoria_ids=[99])

        with pytest.raises(HTTPException) as exc_info:
            await set_categorias_producto(uow, 1, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_lista_vacia_elimina_todas(self):
        """PUT with empty list removes all associations and returns []."""
        from productos.schemas import ProductoCategoriaSetRequest
        from productos.service import set_categorias_producto

        producto = _make_producto(1)
        # After set_categorias, get_categorias returns []
        uow = _make_uow(producto=producto, categorias_list=[])
        data = ProductoCategoriaSetRequest(categoria_ids=[])

        result = await set_categorias_producto(uow, 1, data)

        assert result == []
        uow.producto_categorias.set_categorias.assert_awaited_once_with(1, [])

    @pytest.mark.asyncio
    async def test_reemplazo_exitoso(self):
        """Sets new categories and returns the updated list."""
        from productos.schemas import ProductoCategoriaSetRequest
        from productos.service import set_categorias_producto

        producto = _make_producto(1)
        cat1 = _make_categoria(1, "Bebidas")
        cat2 = _make_categoria(2, "Postres")

        # categorias.get_by_id always returns a valid category
        cat_repo_mock = MagicMock()
        cat_repo_mock.get_by_id = AsyncMock(return_value=cat1)

        # After set, get_categorias returns the new set
        uow = _make_uow(producto=producto, categorias_list=[cat1, cat2])
        uow.categorias = cat_repo_mock

        data = ProductoCategoriaSetRequest(categoria_ids=[1, 2])
        result = await set_categorias_producto(uow, 1, data)

        assert len(result) == 2
        uow.producto_categorias.set_categorias.assert_awaited_once_with(1, [1, 2])


# ---------------------------------------------------------------------------
# Service tests — remove_categoria_producto
# ---------------------------------------------------------------------------


class TestRemoveCategoriasProducto:
    """remove_categoria_producto service function tests."""

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Raises 404 when product does not exist."""
        from productos.service import remove_categoria_producto

        uow = _make_uow(producto=None)

        with pytest.raises(HTTPException) as exc_info:
            await remove_categoria_producto(uow, 999, 1)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_asociacion_no_existe_404(self):
        """Raises 404 when the association does not exist."""
        from productos.service import remove_categoria_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, pivot=None)

        with pytest.raises(HTTPException) as exc_info:
            await remove_categoria_producto(uow, 1, 99)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_elimina_asociacion_exitosamente(self):
        """Calls remove_categoria when the association exists."""
        from productos.service import remove_categoria_producto

        producto = _make_producto(1)
        pivot = _make_pivot(1, 5)
        uow = _make_uow(producto=producto, pivot=pivot)

        await remove_categoria_producto(uow, 1, 5)

        uow.producto_categorias.remove_categoria.assert_awaited_once_with(1, 5)


# ---------------------------------------------------------------------------
# Service tests — get_producto_by_id (enriched)
# ---------------------------------------------------------------------------


class TestGetProductoByIdEnriquecido:
    """get_producto_by_id now includes categorias field."""

    @pytest.mark.asyncio
    async def test_retorna_categorias_vacias_por_defecto(self):
        """ProductoResponse includes empty categorias list when no associations exist."""
        from productos.service import get_producto_by_id

        producto = _make_producto(1, "Alfajor")
        uow = _make_uow(producto=producto, categorias_list=[])

        result = await get_producto_by_id(uow, 1)

        assert result.id == 1
        assert result.nombre == "Alfajor"
        assert result.categorias == []

    @pytest.mark.asyncio
    async def test_retorna_categorias_asociadas(self):
        """ProductoResponse includes populated categorias list."""
        from productos.service import get_producto_by_id

        producto = _make_producto(2, "Medialunas")
        cats = [_make_categoria(3, "Panadería")]
        uow = _make_uow(producto=producto, categorias_list=cats)

        result = await get_producto_by_id(uow, 2)

        assert len(result.categorias) == 1
        assert result.categorias[0].id == 3
        assert result.categorias[0].nombre == "Panadería"

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Still raises 404 when product does not exist."""
        from productos.service import get_producto_by_id

        uow = _make_uow(producto=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_producto_by_id(uow, 404)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Router integration tests — GET /{id}/categorias (public)
# ---------------------------------------------------------------------------


class TestGetCategoriasByProductoRouter:
    """GET /api/v1/productos/{id}/categorias — public endpoint."""

    def test_get_categorias_publico_sin_auth(self):
        """Endpoint is accessible without authentication → 200."""
        from main import app
        from infrastructure.uow import get_uow
        from productos.service import list_categorias_producto

        producto = _make_producto(1)

        async def _fake_uow():
            return _make_uow(producto=producto, categorias_list=[])

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            from unittest.mock import patch, AsyncMock as AM
            with patch(
                "productos.service.list_categorias_producto",
                new=AM(return_value=[]),
            ):
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/productos/1/categorias")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()

    def test_get_categorias_producto_no_existe_404(self):
        """Returns 404 when product does not exist."""
        from main import app
        from infrastructure.uow import get_uow

        async def _fake_uow():
            return _make_uow(producto=None)

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/api/v1/productos/9999/categorias")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Router integration tests — PUT /{id}/categorias (STOCK or ADMIN)
# ---------------------------------------------------------------------------


class TestPutCategoriasRouter:
    """PUT /api/v1/productos/{id}/categorias — requires STOCK or ADMIN."""

    def test_put_sin_auth_retorna_401(self):
        """PUT without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/api/v1/productos/1/categorias",
                json={"categoria_ids": [1]},
            )
        assert response.status_code == 401

    def test_put_rol_client_retorna_403(self):
        """PUT with CLIENT role → 403."""
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
                response = client.put(
                    "/api/v1/productos/1/categorias",
                    json={"categoria_ids": []},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_put_admin_categoria_inexistente_404(self):
        """PUT with non-existent categoria_id → 404."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)

        async def _mock_user():
            return admin_user

        async def _fake_uow():
            return _make_uow(producto=producto, categoria_obj=None)

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/productos/1/categorias",
                    json={"categoria_ids": [999]},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_put_lista_vacia_elimina_asociaciones(self):
        """PUT with empty list removes all categories → 200 with []."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)

        async def _mock_user():
            return admin_user

        async def _fake_uow():
            return _make_uow(producto=producto, categorias_list=[])

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/productos/1/categorias",
                    json={"categoria_ids": []},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()

    def test_put_admin_reemplaza_categorias_exitosamente(self):
        """PUT with valid categories → 200 with category list."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)
        cat1 = _make_categoria(1, "Bebidas")

        # categorias.get_by_id returns a valid category
        cat_repo = MagicMock()
        cat_repo.get_by_id = AsyncMock(return_value=cat1)

        uow_instance = _make_uow(producto=producto, categorias_list=[cat1])
        uow_instance.categorias = cat_repo

        async def _mock_user():
            return admin_user

        async def _fake_uow():
            return uow_instance

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/productos/1/categorias",
                    json={"categoria_ids": [1]},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["nombre"] == "Bebidas"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Router integration tests — DELETE /{id}/categorias/{cat_id}
# ---------------------------------------------------------------------------


class TestDeleteCategoriaRouter:
    """DELETE /api/v1/productos/{id}/categorias/{cat_id} — requires STOCK or ADMIN."""

    def test_delete_sin_auth_retorna_401(self):
        """DELETE without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.delete("/api/v1/productos/1/categorias/1")
        assert response.status_code == 401

    def test_delete_asociacion_no_existe_404(self):
        """DELETE when association does not exist → 404."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)

        async def _mock_user():
            return admin_user

        async def _fake_uow():
            return _make_uow(producto=producto, pivot=None)

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.delete(
                    "/api/v1/productos/1/categorias/99",
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_delete_asociacion_existente_204(self):
        """DELETE when association exists → 204 No Content."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)
        pivot = _make_pivot(1, 5)

        async def _mock_user():
            return admin_user

        async def _fake_uow():
            return _make_uow(producto=producto, pivot=pivot)

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.delete(
                    "/api/v1/productos/1/categorias/5",
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 204
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Router integration test — GET /{id} includes categorias field
# ---------------------------------------------------------------------------


class TestGetProductoByIdIncludesCategorias:
    """GET /api/v1/productos/{id} response must include categorias field."""

    def test_response_incluye_campo_categorias(self):
        """GET /api/v1/productos/{id} includes categorias (empty list) in response."""
        from main import app
        from infrastructure.uow import get_uow

        producto = _make_producto(1, "Medialunas")

        async def _fake_uow():
            return _make_uow(producto=producto, categorias_list=[])

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/api/v1/productos/1")
            assert response.status_code == 200
            data = response.json()
            assert "categorias" in data
            assert isinstance(data["categorias"], list)
        finally:
            app.dependency_overrides.clear()
