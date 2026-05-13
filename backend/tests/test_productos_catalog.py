"""
Unit + integration tests for products-catalog-public change.

Strategy:
- Service tests: mock UnitOfWork with AsyncMock — no real DB.
- Repository tests: mock SQLAlchemy session with MagicMock.
- Router integration tests: FastAPI TestClient + dependency_overrides.

Coverage:
- list_productos with q= text search
- list_productos with categoria_id= filter
- list_productos combined q + categoria_id
- list_productos returns PaginatedProductosResponse envelope
- list_productos without auth returns only disponible=True products (RN-CA08)
- ProductoRepository.list_active with q parameter (ILIKE)
- ProductoRepository.list_active with categoria_id (JOIN)
- ProductoRepository.count_active
- Router GET / with q=test → 200 envelope
- Router GET / with categoria_id=abc → 422
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


def _make_producto(
    id: int = 1,
    nombre: str = "Producto Test",
    disponible: bool = True,
) -> MagicMock:
    """Return a MagicMock that quacks like a Producto instance."""
    p = MagicMock()
    p.id = id
    p.nombre = nombre
    p.descripcion = f"desc-{nombre}"
    p.precio_base = Decimal("10.00")
    p.stock_cantidad = 5
    p.disponible = disponible
    p.imagen_url = None
    p.creado_en = datetime(2026, 1, 1)
    p.actualizado_en = datetime(2026, 1, 1)
    p.eliminado_en = None
    return p


def _make_uow(repo: MagicMock | None = None) -> MagicMock:
    """
    Return a mock UnitOfWork with async context manager support.

    Wires producto_categorias and producto_ingredientes as empty stubs
    (needed by get_producto_by_id enrichment, but not by list_productos).
    """
    uow = MagicMock()
    if repo is None:
        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=[])
        repo.count_active = AsyncMock(return_value=0)
    uow.productos = repo

    pc_repo = MagicMock()
    pc_repo.get_categorias = AsyncMock(return_value=[])
    uow.producto_categorias = pc_repo

    pi_repo = MagicMock()
    pi_repo.get_ingredientes = AsyncMock(return_value=[])
    uow.producto_ingredientes = pi_repo

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
# Service tests — list_productos with q filter
# ---------------------------------------------------------------------------


class TestListProductosConBusqueda:
    """list_productos passes q parameter to repository."""

    @pytest.mark.asyncio
    async def test_q_pizza_llama_repo_con_ese_parametro(self):
        """Service calls list_active(q='pizza') and returns matching products."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        pizza = _make_producto(1, "Pizza Margherita")
        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=[pizza])
        repo.count_active = AsyncMock(return_value=1)
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=20, q="pizza", page=1, size=20)

        assert isinstance(result, PaginatedProductosResponse)
        assert len(result.items) == 1
        assert result.items[0].id == 1
        assert result.items[0].nombre == "Pizza Margherita"
        assert result.total == 1
        repo.list_active.assert_awaited_once()
        call_kwargs = repo.list_active.call_args.kwargs
        assert call_kwargs["q"] == "pizza"

    @pytest.mark.asyncio
    async def test_q_sin_resultados_retorna_envelope_vacio(self):
        """list_productos with q='xyznonexistent' returns empty envelope."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=[])
        repo.count_active = AsyncMock(return_value=0)
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=20, q="xyznonexistent", page=1, size=20)

        assert isinstance(result, PaginatedProductosResponse)
        assert result.items == []
        assert result.total == 0
        assert result.pages == 0


# ---------------------------------------------------------------------------
# Service tests — list_productos with categoria_id filter
# ---------------------------------------------------------------------------


class TestListProductosConCategoriaId:
    """list_productos passes categoria_id parameter to repository."""

    @pytest.mark.asyncio
    async def test_categoria_id_llama_repo_con_ese_parametro(self):
        """Service passes categoria_id=3 to list_active."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        taco = _make_producto(2, "Taco")
        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=[taco])
        repo.count_active = AsyncMock(return_value=1)
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=20, categoria_id=3, page=1, size=20)

        assert isinstance(result, PaginatedProductosResponse)
        assert len(result.items) == 1
        assert result.items[0].id == 2
        assert result.items[0].nombre == "Taco"
        call_kwargs = repo.list_active.call_args.kwargs
        assert call_kwargs["categoria_id"] == 3

    @pytest.mark.asyncio
    async def test_q_y_categoria_id_combinados(self):
        """Service passes both q and categoria_id to list_active simultaneously."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        burrito = _make_producto(3, "Burrito de carne")
        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=[burrito])
        repo.count_active = AsyncMock(return_value=1)
        uow = _make_uow(repo)

        result = await list_productos(
            uow, skip=0, limit=20, q="burrito", categoria_id=2, page=1, size=20
        )

        assert isinstance(result, PaginatedProductosResponse)
        assert len(result.items) == 1
        assert result.items[0].id == 3
        assert result.items[0].nombre == "Burrito de carne"
        call_kwargs = repo.list_active.call_args.kwargs
        assert call_kwargs["q"] == "burrito"
        assert call_kwargs["categoria_id"] == 2


# ---------------------------------------------------------------------------
# Service tests — disponible filter (RN-CA08)
# ---------------------------------------------------------------------------


class TestListProductosDisponibleFilter:
    """list_productos without auth passes incluir_eliminados=False (triggers disponible filter)."""

    @pytest.mark.asyncio
    async def test_sin_autenticacion_filtra_solo_disponibles(self):
        """Public list passes incluir_eliminados=False, repo applies disponible=True filter."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        disponible = _make_producto(1, "Visible", disponible=True)
        repo = MagicMock()
        # Repo only returns disponible products (the filter lives in the repository)
        repo.list_active = AsyncMock(return_value=[disponible])
        repo.count_active = AsyncMock(return_value=1)
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=20, page=1, size=20)

        assert isinstance(result, PaginatedProductosResponse)
        call_kwargs = repo.list_active.call_args.kwargs
        # Service passes incluir_eliminados=False → repo applies disponible=True filter
        assert call_kwargs["incluir_eliminados"] is False


# ---------------------------------------------------------------------------
# Service tests — pagination envelope
# ---------------------------------------------------------------------------


class TestPaginatedEnvelope:
    """list_productos returns correct PaginatedProductosResponse metadata."""

    @pytest.mark.asyncio
    async def test_pages_calculados_correctamente(self):
        """pages = ceil(total / size) is calculated correctly."""
        from productos.service import list_productos
        from productos.schemas import PaginatedProductosResponse

        items = [_make_producto(i) for i in range(1, 6)]  # 5 items
        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=items)
        repo.count_active = AsyncMock(return_value=23)  # total > 1 page
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=5, page=1, size=5)

        assert result.total == 23
        assert result.page == 1
        assert result.size == 5
        assert result.pages == 5  # ceil(23/5) = 5

    @pytest.mark.asyncio
    async def test_pages_cero_cuando_total_cero(self):
        """pages == 0 when total == 0."""
        from productos.service import list_productos

        repo = MagicMock()
        repo.list_active = AsyncMock(return_value=[])
        repo.count_active = AsyncMock(return_value=0)
        uow = _make_uow(repo)

        result = await list_productos(uow, skip=0, limit=20, page=1, size=20)

        assert result.total == 0
        assert result.pages == 0


# ---------------------------------------------------------------------------
# Repository tests — list_active with q (ILIKE)
# ---------------------------------------------------------------------------


class TestProductoRepositoryListActiveConQ:
    """ProductoRepository.list_active applies ILIKE filter when q is given."""

    @pytest.mark.asyncio
    async def test_list_active_con_q_ejecuta_query(self):
        """list_active(q='pizza') calls session.execute and returns scalars."""
        from productos.repository import ProductoRepository

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ProductoRepository(mock_session)
        result = await repo.list_active(skip=0, limit=20, q="pizza")

        assert isinstance(result, list)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_active_con_categoria_id_ejecuta_query(self):
        """list_active(categoria_id=3) calls session.execute with JOIN."""
        from productos.repository import ProductoRepository

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ProductoRepository(mock_session)
        result = await repo.list_active(skip=0, limit=20, categoria_id=3)

        assert isinstance(result, list)
        mock_session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# Repository tests — count_active
# ---------------------------------------------------------------------------


class TestProductoRepositoryCountActive:
    """ProductoRepository.count_active returns integer count."""

    @pytest.mark.asyncio
    async def test_count_active_retorna_entero(self):
        """count_active returns scalar integer from session."""
        from productos.repository import ProductoRepository

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ProductoRepository(mock_session)
        result = await repo.count_active()

        assert result == 42
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_count_active_con_q_ejecuta_query(self):
        """count_active(q='pizza') executes count query with filter."""
        from productos.repository import ProductoRepository

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ProductoRepository(mock_session)
        result = await repo.count_active(q="pizza")

        assert result == 3
        mock_session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# Router integration tests — GET / with new query params
# ---------------------------------------------------------------------------


class TestListProductosRouterEnvelope:
    """GET /api/v1/productos/ returns PaginatedProductosResponse envelope."""

    def test_get_productos_q_retorna_200_con_envelope(self):
        """GET /api/v1/productos?q=test → 200 with envelope shape."""
        from main import app
        from infrastructure.uow import get_uow
        from productos.router import get_optional_user
        from productos.schemas import PaginatedProductosResponse

        _envelope = PaginatedProductosResponse(items=[], total=0, page=1, size=20, pages=0)

        async def _fake_uow():
            return _make_uow()

        async def _no_user():
            return None

        app.dependency_overrides[get_uow] = _fake_uow
        app.dependency_overrides[get_optional_user] = _no_user

        try:
            from unittest.mock import patch, AsyncMock as AM
            with patch(
                "productos.service.list_productos",
                new=AM(return_value=_envelope),
            ):
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/productos/?q=test")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data
            assert "pages" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_productos_categoria_id_invalido_retorna_422(self):
        """GET /api/v1/productos?categoria_id=abc → 422 (not a valid int)."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/productos/?categoria_id=abc")

        assert response.status_code == 422

    def test_get_productos_page_y_size_retorna_200(self):
        """GET /api/v1/productos?page=1&size=5 → 200 with correct pagination metadata."""
        from main import app
        from infrastructure.uow import get_uow
        from productos.router import get_optional_user
        from productos.schemas import PaginatedProductosResponse

        _envelope = PaginatedProductosResponse(
            items=[], total=0, page=1, size=5, pages=0
        )

        async def _fake_uow():
            return _make_uow()

        async def _no_user():
            return None

        app.dependency_overrides[get_uow] = _fake_uow
        app.dependency_overrides[get_optional_user] = _no_user

        try:
            from unittest.mock import patch, AsyncMock as AM
            with patch(
                "productos.service.list_productos",
                new=AM(return_value=_envelope),
            ):
                with TestClient(app, raise_server_exceptions=False) as client:
                    response = client.get("/api/v1/productos/?page=1&size=5")

            assert response.status_code == 200
            data = response.json()
            assert data["size"] == 5
            assert data["page"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_productos_size_mayor_100_retorna_422(self):
        """GET /api/v1/productos?size=200 → 422 (size > 100 is invalid)."""
        from main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/productos/?size=200")

        assert response.status_code == 422
