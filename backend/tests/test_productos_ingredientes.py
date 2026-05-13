"""
Unit + integration tests for products-ingredients-association change.

Strategy:
- Service tests: mock UnitOfWork with AsyncMock — no real DB.
- Router integration tests: FastAPI TestClient + dependency_overrides.

Coverage:
- list_ingredientes_producto
- set_ingredientes_producto
- remove_ingrediente_producto
- get_producto_by_id (enriched with ingredientes)
- list_productos with excluirAlergenos query param
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


def _make_ingrediente(
    id: int = 1,
    nombre: str = "Ingrediente Test",
    es_alergeno: bool = False,
) -> MagicMock:
    """Return a MagicMock that quacks like an Ingrediente instance."""
    i = MagicMock()
    i.id = id
    i.nombre = nombre
    i.es_alergeno = es_alergeno
    i.eliminado_en = None
    return i


def _make_pivot_ing(
    producto_id: int = 1,
    ingrediente_id: int = 1,
    es_removible: bool = False,
) -> MagicMock:
    """Return a MagicMock for a ProductoIngrediente pivot row."""
    p = MagicMock()
    p.producto_id = producto_id
    p.ingrediente_id = ingrediente_id
    p.es_removible = es_removible
    return p


def _make_uow(
    producto=None,
    ingredientes_pairs=None,
    ingrediente_obj=None,
    pivot=None,
    categorias_list=None,
) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    Wires:
    - uow.productos.get_by_id → producto (or None)
    - uow.producto_ingredientes.get_ingredientes → ingredientes_pairs (or [])
    - uow.producto_ingredientes.set_ingredientes → AsyncMock (no-op)
    - uow.producto_ingredientes.get_association → pivot (or None)
    - uow.producto_ingredientes.remove_ingrediente → AsyncMock (no-op)
    - uow.producto_ingredientes.list_active_excluding_alergenos → [] (default)
    - uow.ingredientes.get_by_id → ingrediente_obj (or a real mock Ingrediente)
    - uow.producto_categorias.get_categorias → categorias_list (or [])
    """
    uow = MagicMock()

    # productos repo
    productos_repo = MagicMock()
    productos_repo.get_by_id = AsyncMock(return_value=producto)
    productos_repo.list_active = AsyncMock(return_value=[producto] if producto else [])
    uow.productos = productos_repo

    # producto_ingredientes repo
    pi_repo = MagicMock()
    pi_repo.get_ingredientes = AsyncMock(return_value=ingredientes_pairs or [])
    pi_repo.set_ingredientes = AsyncMock(return_value=None)
    pi_repo.get_association = AsyncMock(return_value=pivot)
    pi_repo.remove_ingrediente = AsyncMock(return_value=None)
    pi_repo.list_active_excluding_alergenos = AsyncMock(return_value=[])
    uow.producto_ingredientes = pi_repo

    # ingredientes repo
    ing_repo = MagicMock()
    ing_repo.get_by_id = AsyncMock(return_value=ingrediente_obj)
    uow.ingredientes = ing_repo

    # producto_categorias repo
    pc_repo = MagicMock()
    pc_repo.get_categorias = AsyncMock(return_value=categorias_list or [])
    uow.producto_categorias = pc_repo

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
# Service tests — list_ingredientes_producto
# ---------------------------------------------------------------------------


class TestListIngredientesProducto:
    """list_ingredientes_producto service function tests."""

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Raises 404 when product does not exist."""
        from productos.service import list_ingredientes_producto

        uow = _make_uow(producto=None)

        with pytest.raises(HTTPException) as exc_info:
            await list_ingredientes_producto(uow, 999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_producto_sin_ingredientes_retorna_lista_vacia(self):
        """Returns empty list when product has no ingredients."""
        from productos.service import list_ingredientes_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, ingredientes_pairs=[])

        result = await list_ingredientes_producto(uow, 1)

        assert result == []

    @pytest.mark.asyncio
    async def test_producto_con_ingredientes_retorna_lista(self):
        """Returns compact list of ingredients with es_removible from pivot."""
        from productos.service import list_ingredientes_producto

        producto = _make_producto(1)
        ing1 = _make_ingrediente(1, "Gluten", es_alergeno=True)
        ing2 = _make_ingrediente(2, "Queso", es_alergeno=False)
        pairs = [(ing1, True), (ing2, False)]
        uow = _make_uow(producto=producto, ingredientes_pairs=pairs)

        result = await list_ingredientes_producto(uow, 1)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].nombre == "Gluten"
        assert result[0].es_alergeno is True
        assert result[0].es_removible is True
        assert result[1].id == 2
        assert result[1].nombre == "Queso"
        assert result[1].es_alergeno is False
        assert result[1].es_removible is False


# ---------------------------------------------------------------------------
# Service tests — set_ingredientes_producto
# ---------------------------------------------------------------------------


class TestSetIngredientesProducto:
    """set_ingredientes_producto service function tests."""

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Raises 404 when product does not exist."""
        from productos.schemas import ProductoIngredienteSetRequest, IngredienteAsociacion
        from productos.service import set_ingredientes_producto

        uow = _make_uow(producto=None)
        data = ProductoIngredienteSetRequest(
            ingredientes=[IngredienteAsociacion(ingrediente_id=1, es_removible=False)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await set_ingredientes_producto(uow, 999, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_ingrediente_inexistente_404(self):
        """Raises 404 if any ingrediente_id does not exist."""
        from productos.schemas import ProductoIngredienteSetRequest, IngredienteAsociacion
        from productos.service import set_ingredientes_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, ingrediente_obj=None)
        data = ProductoIngredienteSetRequest(
            ingredientes=[IngredienteAsociacion(ingrediente_id=99, es_removible=False)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await set_ingredientes_producto(uow, 1, data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_lista_vacia_elimina_todas(self):
        """PUT with empty list removes all associations and returns []."""
        from productos.schemas import ProductoIngredienteSetRequest
        from productos.service import set_ingredientes_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, ingredientes_pairs=[])
        data = ProductoIngredienteSetRequest(ingredientes=[])

        result = await set_ingredientes_producto(uow, 1, data)

        assert result == []
        uow.producto_ingredientes.set_ingredientes.assert_awaited_once_with(1, [])

    @pytest.mark.asyncio
    async def test_reemplazo_exitoso(self):
        """Sets new ingredients and returns the updated list."""
        from productos.schemas import ProductoIngredienteSetRequest, IngredienteAsociacion
        from productos.service import set_ingredientes_producto

        producto = _make_producto(1)
        ing1 = _make_ingrediente(1, "Harina", es_alergeno=True)
        ing2 = _make_ingrediente(2, "Azucar", es_alergeno=False)

        ing_repo_mock = MagicMock()
        ing_repo_mock.get_by_id = AsyncMock(return_value=ing1)

        pairs = [(ing1, True), (ing2, False)]
        uow = _make_uow(producto=producto, ingredientes_pairs=pairs)
        uow.ingredientes = ing_repo_mock

        data = ProductoIngredienteSetRequest(
            ingredientes=[
                IngredienteAsociacion(ingrediente_id=1, es_removible=True),
                IngredienteAsociacion(ingrediente_id=2, es_removible=False),
            ]
        )
        result = await set_ingredientes_producto(uow, 1, data)

        assert len(result) == 2
        uow.producto_ingredientes.set_ingredientes.assert_awaited_once_with(
            1,
            [
                {"ingrediente_id": 1, "es_removible": True},
                {"ingrediente_id": 2, "es_removible": False},
            ],
        )


# ---------------------------------------------------------------------------
# Service tests — remove_ingrediente_producto
# ---------------------------------------------------------------------------


class TestRemoveIngredienteProducto:
    """remove_ingrediente_producto service function tests."""

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Raises 404 when product does not exist."""
        from productos.service import remove_ingrediente_producto

        uow = _make_uow(producto=None)

        with pytest.raises(HTTPException) as exc_info:
            await remove_ingrediente_producto(uow, 999, 1)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_asociacion_no_existe_404(self):
        """Raises 404 when the association does not exist."""
        from productos.service import remove_ingrediente_producto

        producto = _make_producto(1)
        uow = _make_uow(producto=producto, pivot=None)

        with pytest.raises(HTTPException) as exc_info:
            await remove_ingrediente_producto(uow, 1, 99)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_elimina_asociacion_exitosamente(self):
        """Calls remove_ingrediente when the association exists."""
        from productos.service import remove_ingrediente_producto

        producto = _make_producto(1)
        pivot = _make_pivot_ing(1, 5, False)
        uow = _make_uow(producto=producto, pivot=pivot)

        await remove_ingrediente_producto(uow, 1, 5)

        uow.producto_ingredientes.remove_ingrediente.assert_awaited_once_with(1, 5)


# ---------------------------------------------------------------------------
# Service tests — get_producto_by_id enriched with ingredientes
# ---------------------------------------------------------------------------


class TestGetProductoByIdEnriquecido:
    """get_producto_by_id response includes ingredientes field."""

    @pytest.mark.asyncio
    async def test_retorna_ingredientes_vacios_por_defecto(self):
        """ProductoResponse includes empty ingredientes list when no associations exist."""
        from productos.service import get_producto_by_id

        producto = _make_producto(1, "Alfajor")
        uow = _make_uow(producto=producto, ingredientes_pairs=[])

        result = await get_producto_by_id(uow, 1)

        assert result.id == 1
        assert result.nombre == "Alfajor"
        assert result.ingredientes == []

    @pytest.mark.asyncio
    async def test_retorna_ingredientes_asociados_con_es_removible(self):
        """ProductoResponse includes populated ingredientes list with correct es_removible."""
        from productos.service import get_producto_by_id

        producto = _make_producto(2, "Pizza")
        ing = _make_ingrediente(3, "Gluten", es_alergeno=True)
        pairs = [(ing, True)]
        uow = _make_uow(producto=producto, ingredientes_pairs=pairs)

        result = await get_producto_by_id(uow, 2)

        assert len(result.ingredientes) == 1
        assert result.ingredientes[0].id == 3
        assert result.ingredientes[0].nombre == "Gluten"
        assert result.ingredientes[0].es_alergeno is True
        assert result.ingredientes[0].es_removible is True

    @pytest.mark.asyncio
    async def test_producto_no_existe_404(self):
        """Still raises 404 when product does not exist."""
        from productos.service import get_producto_by_id

        uow = _make_uow(producto=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_producto_by_id(uow, 404)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Router integration tests — GET /{id}/ingredientes (public)
# ---------------------------------------------------------------------------


class TestGetIngredientesByProductoRouter:
    """GET /api/v1/productos/{id}/ingredientes — public endpoint."""

    def test_get_ingredientes_publico_sin_auth(self):
        """Endpoint is accessible without authentication → 200."""
        from main import app
        from infrastructure.uow import get_uow
        from unittest.mock import patch, AsyncMock as AM

        producto = _make_producto(1)

        async def _fake_uow():
            return _make_uow(producto=producto, ingredientes_pairs=[])

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with patch(
                "productos.service.list_ingredientes_producto",
                new=AM(return_value=[]),
            ):
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/productos/1/ingredientes")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()

    def test_get_ingredientes_producto_no_existe_404(self):
        """Returns 404 when product does not exist."""
        from main import app
        from infrastructure.uow import get_uow

        async def _fake_uow():
            return _make_uow(producto=None)

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/api/v1/productos/9999/ingredientes")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Router integration tests — PUT /{id}/ingredientes (STOCK or ADMIN)
# ---------------------------------------------------------------------------


class TestPutIngredientesRouter:
    """PUT /api/v1/productos/{id}/ingredientes — requires STOCK or ADMIN."""

    def test_put_sin_auth_retorna_401(self):
        """PUT without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/api/v1/productos/1/ingredientes",
                json={"ingredientes": []},
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
                    "/api/v1/productos/1/ingredientes",
                    json={"ingredientes": []},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_put_lista_vacia_elimina_asociaciones(self):
        """PUT with empty list removes all ingredients → 200 with []."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)

        async def _mock_user():
            return admin_user

        async def _fake_uow():
            return _make_uow(producto=producto, ingredientes_pairs=[])

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[infra_get_current_user] = _mock_user
        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/api/v1/productos/1/ingredientes",
                    json={"ingredientes": []},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()

    def test_put_admin_reemplaza_ingredientes_exitosamente(self):
        """PUT with valid ingredients → 200 with ingredient list."""
        from main import app
        from core.dependencies import get_current_user
        from infrastructure.dependencies import get_current_user as infra_get_current_user
        from infrastructure.uow import get_uow

        admin_user = _make_user(["ADMIN"])
        producto = _make_producto(1)
        ing1 = _make_ingrediente(1, "Harina", es_alergeno=True)

        ing_repo = MagicMock()
        ing_repo.get_by_id = AsyncMock(return_value=ing1)

        pairs = [(ing1, True)]
        uow_instance = _make_uow(producto=producto, ingredientes_pairs=pairs)
        uow_instance.ingredientes = ing_repo

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
                    "/api/v1/productos/1/ingredientes",
                    json={"ingredientes": [{"ingrediente_id": 1, "es_removible": True}]},
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["nombre"] == "Harina"
            assert data[0]["es_alergeno"] is True
            assert data[0]["es_removible"] is True
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Router integration tests — DELETE /{id}/ingredientes/{ing_id}
# ---------------------------------------------------------------------------


class TestDeleteIngredienteRouter:
    """DELETE /api/v1/productos/{id}/ingredientes/{ing_id} — requires STOCK or ADMIN."""

    def test_delete_sin_auth_retorna_401(self):
        """DELETE without token → 401."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.delete("/api/v1/productos/1/ingredientes/1")
        assert response.status_code == 401

    def test_delete_rol_client_retorna_403(self):
        """DELETE with CLIENT role → 403."""
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
                response = client.delete(
                    "/api/v1/productos/1/ingredientes/1",
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

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
                    "/api/v1/productos/1/ingredientes/99",
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
        pivot = _make_pivot_ing(1, 5, False)

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
                    "/api/v1/productos/1/ingredientes/5",
                    headers={"Authorization": "Bearer fake.token.here"},
                )
            assert response.status_code == 204
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Router integration tests — GET / with excluirAlergenos
# ---------------------------------------------------------------------------


class TestListProductosExcluirAlergenos:
    """GET /api/v1/productos/?excluirAlergenos=... — allergen filter."""

    def test_sin_parametro_retorna_lista_normal(self):
        """Without excluirAlergenos param, normal list_active is called."""
        from main import app
        from infrastructure.uow import get_uow

        producto = _make_producto(1, "Sandwich")

        async def _fake_uow():
            return _make_uow(producto=producto)

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/api/v1/productos/")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            app.dependency_overrides.clear()

    def test_con_ids_validos_retorna_200(self):
        """excluirAlergenos with valid IDs → 200."""
        from main import app
        from infrastructure.uow import get_uow

        producto = _make_producto(1, "Sin Gluten")
        uow_instance = _make_uow(producto=producto)
        uow_instance.producto_ingredientes.list_active_excluding_alergenos = AsyncMock(
            return_value=[producto]
        )

        async def _fake_uow():
            return uow_instance

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/api/v1/productos/?excluirAlergenos=1,3,7")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_con_valor_no_entero_retorna_422(self):
        """excluirAlergenos with non-integer value → 422."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/productos/?excluirAlergenos=abc,1")
        assert response.status_code == 422

    def test_con_mas_de_50_ids_retorna_422(self):
        """excluirAlergenos with more than 50 IDs → 422."""
        from main import app

        ids_str = ",".join(str(i) for i in range(1, 52))  # 51 IDs
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(f"/api/v1/productos/?excluirAlergenos={ids_str}")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Router integration test — GET /{id} includes ingredientes field
# ---------------------------------------------------------------------------


class TestGetProductoByIdIncludesIngredientes:
    """GET /api/v1/productos/{id} response must include ingredientes field."""

    def test_response_incluye_campo_ingredientes(self):
        """GET /api/v1/productos/{id} includes ingredientes (empty list) in response."""
        from main import app
        from infrastructure.uow import get_uow

        producto = _make_producto(1, "Medialunas")

        async def _fake_uow():
            return _make_uow(producto=producto, ingredientes_pairs=[])

        app.dependency_overrides[get_uow] = _fake_uow
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/api/v1/productos/1")
            assert response.status_code == 200
            data = response.json()
            assert "ingredientes" in data
            assert isinstance(data["ingredientes"], list)
        finally:
            app.dependency_overrides.clear()
