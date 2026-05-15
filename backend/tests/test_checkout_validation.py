"""
Tests for POST /api/v1/pedidos/validar — pre-checkout cart validation.

Strategy:
  - Uses FastAPI TestClient with dependency_overrides to mock:
      * get_current_user (auth) — avoids DB / JWT
      * get_uow (UnitOfWork) — avoids DB; injects AsyncMock repositories
  - Tests each scenario from the spec (checkout-pre-validation):
      5.2  carrito vacío → 422
      5.3  usuario sin direcciones → 422
      5.4  carrito válido (stock OK, precio OK) → 200 vacío
      5.5  stock insuficiente → 200 con stockInsuficiente
      5.6  precio drift > 0.01 → 200 con cambiosDePrecio
      5.7  producto_id inexistente → 200 con productosInvalidos
      5.8  producto disponible=False → 200 con productosInvalidos
      5.9  sin JWT → 401
      5.10 rol ADMIN → 403
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from core.dependencies import get_current_user
from infrastructure.dependencies import get_current_user as infra_get_current_user
from infrastructure.uow import get_uow, UnitOfWork


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(roles: list[str], user_id: int = 2) -> MagicMock:
    """Return a mock Usuario with given roles and id."""
    user = MagicMock()
    user.id = user_id
    user.activo = True
    user.eliminado_en = None
    user.roles = [MagicMock(nombre=r) for r in roles]
    return user


def _make_producto(
    id: int,
    nombre: str = "Producto Test",
    precio: Decimal = Decimal("100.00"),
    stock: int = 10,
    disponible: bool = True,
    eliminado_en=None,
) -> MagicMock:
    """Return a mock Producto SQLModel instance."""
    p = MagicMock()
    p.id = id
    p.nombre = nombre
    p.precio_base = precio
    p.stock_cantidad = stock
    p.disponible = disponible
    p.eliminado_en = eliminado_en
    return p


def _make_uow(
    productos: list,
    count_active_addresses: int = 1,
) -> MagicMock:
    """
    Build a mock UnitOfWork that:
      - uow.productos.get_by_ids(...) → productos list
      - uow.direcciones.count_active_by_usuario(...) → count_active_addresses
    """
    uow = MagicMock(spec=UnitOfWork)

    # Async context manager support
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)

    # productos repo
    productos_repo = AsyncMock()
    productos_repo.get_by_ids = AsyncMock(return_value=productos)
    uow.productos = productos_repo

    # direcciones repo
    direcciones_repo = AsyncMock()
    direcciones_repo.count_active_by_usuario = AsyncMock(return_value=count_active_addresses)
    uow.direcciones = direcciones_repo

    return uow


def _override_auth(roles: list[str], user_id: int = 2):
    """Override both get_current_user dependencies with a mock user."""
    user = _make_user(roles, user_id=user_id)

    async def _mock():
        return user

    app.dependency_overrides[get_current_user] = _mock
    app.dependency_overrides[infra_get_current_user] = _mock
    return user


def _override_uow(uow_mock: MagicMock):
    """Override get_uow with the given mock."""
    def _factory():
        return uow_mock

    app.dependency_overrides[get_uow] = _factory


def _clear_overrides():
    app.dependency_overrides.clear()


# Payload helpers
VALID_ITEM = {"producto_id": 1, "cantidad": 2, "precio_carrito": "100.00"}
VALID_PAYLOAD = {"items": [VALID_ITEM], "direccion_id": 1}


# ---------------------------------------------------------------------------
# 5.2  Test: carrito vacío → 422
# ---------------------------------------------------------------------------


class TestCarritoVacio:
    """POST /api/v1/pedidos/validar with empty items → HTTP 422."""

    def test_empty_items_returns_422(self):
        """ValidarCarritoRequest requires min_length=1 — Pydantic rejects empty list."""
        _override_auth(["CLIENT"])
        uow_mock = _make_uow(productos=[], count_active_addresses=1)
        _override_uow(uow_mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json={"items": [], "direccion_id": 1},
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 422
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.3  Test: usuario sin direcciones → 422
# ---------------------------------------------------------------------------


class TestSinDirecciones:
    """User with zero active addresses → HTTP 422."""

    def test_no_addresses_returns_422(self):
        """Service raises 422 when address count is 0."""
        _override_auth(["CLIENT"])
        producto = _make_producto(id=1)
        uow_mock = _make_uow(productos=[producto], count_active_addresses=0)
        _override_uow(uow_mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=VALID_PAYLOAD,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 422
            body = response.json()
            # RFC 7807: detail field describes the issue
            detail = body.get("detail", {})
            if isinstance(detail, dict):
                assert "dirección" in detail.get("detail", "").lower() or "direcci" in str(detail).lower()
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.4  Test: carrito con stock suficiente y precios sin cambios → 200 vacío
# ---------------------------------------------------------------------------


class TestCarritoValido:
    """Valid cart with no issues → HTTP 200 with all empty arrays."""

    def test_clean_cart_returns_200_with_empty_arrays(self):
        """No issues → 200, all warning lists empty."""
        _override_auth(["CLIENT"])
        producto = _make_producto(id=1, precio=Decimal("100.00"), stock=10)
        uow_mock = _make_uow(productos=[producto], count_active_addresses=1)
        _override_uow(uow_mock)
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=VALID_PAYLOAD,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert body["stock_insuficiente"] == []
            assert body["productos_invalidos"] == []
            assert body["cambios_de_precio"] == []
            assert body["carrito_vacio"] is False
            assert body["sin_direccion"] is False
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.5  Test: stock insuficiente → 200 con stockInsuficiente
# ---------------------------------------------------------------------------


class TestStockInsuficiente:
    """Item quantity exceeds available stock → 200 with stock_insuficiente populated."""

    def test_insufficient_stock_appears_in_response(self):
        """Requesting 10 when only 3 in stock → stock_insuficiente includes that product."""
        _override_auth(["CLIENT"])
        producto = _make_producto(id=1, nombre="Hamburguesa", stock=3)
        uow_mock = _make_uow(productos=[producto], count_active_addresses=1)
        _override_uow(uow_mock)
        payload = {
            "items": [{"producto_id": 1, "cantidad": 10, "precio_carrito": "100.00"}],
            "direccion_id": 1,
        }
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=payload,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert len(body["stock_insuficiente"]) == 1
            shortage = body["stock_insuficiente"][0]
            assert shortage["producto_id"] == 1
            assert shortage["stock_actual"] == 3
            assert shortage["cantidad_solicitada"] == 10
            # Product is not in invalidos (stock shortage ≠ invalid product)
            assert 1 not in body["productos_invalidos"]
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.6  Test: precio drift > 0.01 → 200 con cambiosDePrecio
# ---------------------------------------------------------------------------


class TestCambioPrecio:
    """Cart price drifted more than 0.01 from current DB price → cambios_de_precio."""

    def test_price_drift_detected(self):
        """precio_carrito=100.00, actual=105.00 → cambios_de_precio populated."""
        _override_auth(["CLIENT"])
        producto = _make_producto(id=1, precio=Decimal("105.00"), stock=10)
        uow_mock = _make_uow(productos=[producto], count_active_addresses=1)
        _override_uow(uow_mock)
        payload = {
            "items": [{"producto_id": 1, "cantidad": 1, "precio_carrito": "100.00"}],
            "direccion_id": 1,
        }
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=payload,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert len(body["cambios_de_precio"]) == 1
            change = body["cambios_de_precio"][0]
            assert change["producto_id"] == 1
            assert float(change["precio_carrito"]) == pytest.approx(100.00, abs=0.001)
            assert float(change["precio_actual"]) == pytest.approx(105.00, abs=0.001)
        finally:
            _clear_overrides()

    def test_price_within_tolerance_not_flagged(self):
        """Difference of exactly 0.01 is within tolerance — no price drift reported."""
        _override_auth(["CLIENT"])
        # Price diff = 0.01 exactly — should NOT flag as drift (> 0.01 required)
        producto = _make_producto(id=1, precio=Decimal("100.01"), stock=10)
        uow_mock = _make_uow(productos=[producto], count_active_addresses=1)
        _override_uow(uow_mock)
        payload = {
            "items": [{"producto_id": 1, "cantidad": 1, "precio_carrito": "100.00"}],
            "direccion_id": 1,
        }
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=payload,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert body["cambios_de_precio"] == []
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.7  Test: producto_id inexistente → 200 con productosInvalidos
# ---------------------------------------------------------------------------


class TestProductoInexistente:
    """producto_id not found in DB → HTTP 200 with that ID in productos_invalidos."""

    def test_missing_product_id_in_invalidos(self):
        """get_by_ids returns empty list → product 99 not found → invalidos."""
        _override_auth(["CLIENT"])
        # Return empty list — product 99 doesn't exist
        uow_mock = _make_uow(productos=[], count_active_addresses=1)
        _override_uow(uow_mock)
        payload = {
            "items": [{"producto_id": 99, "cantidad": 1, "precio_carrito": "50.00"}],
            "direccion_id": 1,
        }
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=payload,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert 99 in body["productos_invalidos"]
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.8  Test: producto con disponible=False → 200 con productosInvalidos
# ---------------------------------------------------------------------------


class TestProductoNoDisponible:
    """Product with disponible=False → HTTP 200 with that ID in productos_invalidos."""

    def test_unavailable_product_in_invalidos(self):
        """disponible=False product → invalidos."""
        _override_auth(["CLIENT"])
        producto = _make_producto(id=5, disponible=False)
        uow_mock = _make_uow(productos=[producto], count_active_addresses=1)
        _override_uow(uow_mock)
        payload = {
            "items": [{"producto_id": 5, "cantidad": 1, "precio_carrito": "100.00"}],
            "direccion_id": 1,
        }
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=payload,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert 5 in body["productos_invalidos"]
            # Should NOT appear in stock_insuficiente (it's invalid, not just low stock)
            assert all(s["producto_id"] != 5 for s in body["stock_insuficiente"])
        finally:
            _clear_overrides()

    def test_soft_deleted_product_in_invalidos(self):
        """eliminado_en IS NOT NULL → invalidos."""
        from datetime import datetime
        _override_auth(["CLIENT"])
        producto = _make_producto(id=7, disponible=True, eliminado_en=datetime.utcnow())
        uow_mock = _make_uow(productos=[producto], count_active_addresses=1)
        _override_uow(uow_mock)
        payload = {
            "items": [{"producto_id": 7, "cantidad": 1, "precio_carrito": "100.00"}],
            "direccion_id": 1,
        }
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=payload,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 200
            body = response.json()
            assert 7 in body["productos_invalidos"]
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.9  Test: sin JWT → 401
# ---------------------------------------------------------------------------


class TestSinJWT:
    """Request without Authorization header → HTTP 401."""

    def test_no_token_returns_401(self):
        """No Authorization header → core.dependencies._extract_token raises 401."""
        _clear_overrides()
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=VALID_PAYLOAD,
                )
            assert response.status_code == 401
        finally:
            _clear_overrides()


# ---------------------------------------------------------------------------
# 5.10 Test: rol ADMIN → 403
# ---------------------------------------------------------------------------


class TestRolIncorrecto:
    """User with ADMIN role (not CLIENT) on /validar → HTTP 403."""

    def test_admin_role_returns_403(self):
        """require_role(['CLIENT']) → ADMIN → 403."""
        _override_auth(["ADMIN"])
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=VALID_PAYLOAD,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 403
        finally:
            _clear_overrides()

    def test_stock_role_returns_403(self):
        """STOCK role → 403."""
        _override_auth(["STOCK"])
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/pedidos/validar",
                    json=VALID_PAYLOAD,
                    headers={"Authorization": "Bearer fake.token"},
                )
            assert response.status_code == 403
        finally:
            _clear_overrides()
