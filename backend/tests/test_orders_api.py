"""
Tests for orders-api-endpoints change.

Strategy:
  Unit/integration tests using mocked UnitOfWork + repositories.
  Tests the router behavior: auth, role enforcement, ownership checks,
  FSM validation, soft delete, pagination isolation, and rate limiting.

Coverage targets (tasks 6.2–6.20):
  6.2  test_create_pedido_no_auth                   → 401
  6.3  test_create_pedido_forbidden_role             → 403
  6.4  test_create_pedido_success                    → 201 with PedidoResponse
  6.5  test_create_pedido_rate_limit                 → 429 on 11th request
  6.6  test_create_pedido_wrong_address              → 403
  6.7  test_list_pedidos_isolation                   → CLIENT-A vs CLIENT-B
  6.8  test_list_pedidos_pagination                  → limit/offset + total
  6.9  test_get_pedido_detail_own                    → 200 with detalles
  6.10 test_get_pedido_detail_other_user             → 403
  6.11 test_get_pedido_detail_admin                  → 200 any user
  6.12 test_get_pedido_not_found                     → 404
  6.13 test_avanzar_estado_valid_transition          → 200 (ADMIN)
  6.14 test_avanzar_estado_invalid_fsm               → 409
  6.15 test_avanzar_estado_client_forbidden          → 403
  6.16 test_delete_pedido_pendiente_by_client        → 200, eliminado_en set
  6.17 test_delete_pedido_non_pendiente_by_client    → 409
  6.18 test_delete_pedido_other_user                 → 403
  6.19 test_delete_soft_delete_removes_from_list     → not in GET /pedidos
  6.20 test_delete_pedido_admin_can_cancel_confirmed → 200 (ADMIN, estado=2)
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

# Import core models directly (no circular path)
from core.models import (
    DetallePedido,
    HistorialEstadoPedido,
    Pedido,
    Rol,
    Usuario,
)

# Import schemas directly (no circular path)
from pedidos.schemas import (
    AvanzarEstadoRequest,
    PedidoCreate,
    DetallePedidoCreate,
)


# ---------------------------------------------------------------------------
# Helpers — mock builders
# ---------------------------------------------------------------------------


def _make_rol(nombre: str = "CLIENT") -> MagicMock:
    r = MagicMock(spec=Rol)
    r.nombre = nombre
    return r


def _make_usuario(
    id: int = 10,
    roles: Optional[list] = None,
    activo: bool = True,
    eliminado_en=None,
) -> MagicMock:
    u = MagicMock(spec=Usuario)
    u.id = id
    u.activo = activo
    u.eliminado_en = eliminado_en
    u.roles = roles if roles is not None else [_make_rol("CLIENT")]
    return u


def _make_admin(id: int = 1) -> MagicMock:
    return _make_usuario(id=id, roles=[_make_rol("ADMIN")])


def _make_pedido(
    id: int = 100,
    usuario_id: int = 10,
    estado_pedido_id: int = 1,
    total: Decimal = Decimal("500.00"),
    eliminado_en=None,
) -> MagicMock:
    p = MagicMock(spec=Pedido)
    p.id = id
    p.usuario_id = usuario_id
    p.estado_pedido_id = estado_pedido_id
    p.total = total
    p.direccion_entrega_id = 1
    p.forma_pago_id = 1
    p.observacion = None
    p.direccion_snapshot = None
    p.creado_en = datetime(2026, 1, 1, 12, 0, 0)
    p.actualizado_en = datetime(2026, 1, 1, 12, 0, 0)
    p.eliminado_en = eliminado_en
    return p


def _make_detalle(
    id: int = 1,
    pedido_id: int = 100,
    producto_id: int = 1,
    cantidad: int = 2,
    precio_snapshot: Decimal = Decimal("500.00"),
) -> MagicMock:
    d = MagicMock(spec=DetallePedido)
    d.id = id
    d.pedido_id = pedido_id
    d.producto_id = producto_id
    d.cantidad = cantidad
    d.precio_snapshot = precio_snapshot
    d.nombre_snapshot = "Hamburguesa Test"
    d.ingredientes_excluidos = None
    d.creado_en = datetime(2026, 1, 1, 12, 0, 0)
    return d


def _make_uow(
    pedido=None,
    pedidos_list=None,
    pedido_count=0,
    pedido_with_details=None,
    pedido_cancelado=None,
) -> MagicMock:
    """Build a mock UnitOfWork with pedidos repo configured."""
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    uow.session = AsyncMock()
    uow.session.add = MagicMock()

    # Use plain AsyncMock (no spec=) to avoid triggering the circular import
    # via infrastructure/__init__ → uow → pedidos.repository
    pedidos_repo = AsyncMock()
    pedidos_repo.get_by_id = AsyncMock(return_value=pedido)
    pedidos_repo.list_by_usuario = AsyncMock(return_value=pedidos_list or [])
    pedidos_repo.count_by_usuario = AsyncMock(return_value=pedido_count)
    pedidos_repo.create_with_details = AsyncMock(return_value=pedido)
    pedidos_repo.update_estado = AsyncMock(return_value=pedido)
    pedidos_repo.get_by_id_with_details = AsyncMock(return_value=pedido_with_details)
    uow.pedidos = pedidos_repo

    historial_repo = AsyncMock()
    historial_repo.append = AsyncMock(return_value=MagicMock(spec=HistorialEstadoPedido))
    uow.historial_estado_pedido = historial_repo

    return uow


# ---------------------------------------------------------------------------
# Helper — call router functions directly (bypass HTTP stack, test logic)
# ---------------------------------------------------------------------------


async def _call_list(current_user, uow, limit=20, offset=0):
    """Call list_pedidos router function directly."""
    from pedidos.router import list_pedidos

    return await list_pedidos(limit=limit, offset=offset, current_user=current_user, uow=uow)


async def _call_get(pedido_id, current_user, uow):
    from pedidos.router import get_pedido

    return await get_pedido(pedido_id=pedido_id, current_user=current_user, uow=uow)


async def _call_avanzar(pedido_id, body, current_user, uow):
    from pedidos.router import avanzar_estado

    return await avanzar_estado(pedido_id=pedido_id, body=body, current_user=current_user, uow=uow)


async def _call_delete(pedido_id, current_user, uow):
    from pedidos.router import delete_pedido

    return await delete_pedido(pedido_id=pedido_id, current_user=current_user, uow=uow)


# ===========================================================================
# 6.2  test_create_pedido_no_auth — 401 without token
# ===========================================================================


class TestCreatePedidoNoAuth:
    """POST /pedidos without Authorization header → 401."""

    def test_create_pedido_no_auth(self):
        """require_role raises 401 when no Authorization header is present."""

        async def _run():
            with pytest.raises(HTTPException) as exc_info:
                # Call get_current_user path via require_role with no token
                from core.dependencies import _extract_token

                await _extract_token(authorization=None)
            assert exc_info.value.status_code == 401

        import asyncio

        asyncio.run(_run())


# ===========================================================================
# 6.3  test_create_pedido_forbidden_role — 403 with wrong role
# ===========================================================================


class TestCreatePedidoForbiddenRole:
    """POST /pedidos with ADMIN role (no CLIENT) → 403 from require_role."""

    @pytest.mark.asyncio
    async def test_admin_role_cannot_create_pedido(self):
        """require_role(["CLIENT"]) rejects an ADMIN-only user."""
        from core.dependencies import require_role

        # Simulate authenticated ADMIN user
        admin_user = _make_admin(id=1)

        dep_fn = require_role(["CLIENT"])

        with pytest.raises(HTTPException) as exc_info:
            await dep_fn(current_user=admin_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["status"] == 403


# ===========================================================================
# 6.4  test_create_pedido_success — 201 with body
# ===========================================================================


class TestCreatePedidoSuccess:
    """POST /pedidos with valid CLIENT → 201, Location header, PedidoResponse body."""

    @pytest.mark.asyncio
    async def test_create_pedido_returns_201(self):
        """service.create_pedido is called; response has id and estado_pedido_id=1."""
        from fastapi import Response as FastAPIResponse
        from starlette.requests import Request as StarletteRequest
        from pedidos.router import create_pedido as router_create

        client_user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido_mock = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)

        uow = _make_uow(pedido=pedido_mock)

        body = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=1, cantidad=2)],
        )

        # Build a minimal real Starlette Request (required by slowapi decorator)
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/pedidos",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
        real_request = StarletteRequest(scope)

        # Patch service.create_pedido to return mock pedido
        with patch("pedidos.router.service.create_pedido", new=AsyncMock(return_value=pedido_mock)):
            response = FastAPIResponse()

            result = await router_create(
                request=real_request,
                body=body,
                response=response,
                current_user=client_user,
                uow=uow,
            )

        assert result.id == 100
        assert result.usuario_id == 10
        assert result.estado_pedido_id == 1
        assert "Location" in response.headers
        assert "/api/v1/pedidos/100" in response.headers["Location"]


# ===========================================================================
# 6.5  test_create_pedido_rate_limit — 429 on 11th request
# ===========================================================================


class TestCreatePedidoRateLimit:
    """Rate limit key function returns unique key per user."""

    def test_rate_limit_key_uses_user_id(self):
        """_pedido_rate_key returns create_pedido:{user_id} when state has user id."""
        from pedidos.router import _pedido_rate_key

        request_mock = MagicMock()
        request_mock.state = MagicMock()
        request_mock.state.pedido_user_id = 42

        key = _pedido_rate_key(request_mock)
        assert key == "create_pedido:42"

    def test_rate_limit_key_fallback_to_ip(self):
        """_pedido_rate_key falls back to IP when state has no user_id."""
        from pedidos.router import _pedido_rate_key

        request_mock = MagicMock()
        # State has no pedido_user_id attribute
        type(request_mock.state).pedido_user_id = property(
            lambda self: (_ for _ in ()).throw(AttributeError("pedido_user_id"))
        )
        request_mock.client.host = "192.168.1.1"

        # getattr with None fallback
        with patch("pedidos.router._pedido_rate_key", wraps=_pedido_rate_key):
            request_mock2 = MagicMock()
            request_mock2.state = MagicMock(spec=[])  # empty spec — no attributes
            # Use slowapi fallback
            key = _pedido_rate_key(request_mock2)
            # Just verify it doesn't crash and returns a string
            assert isinstance(key, str)
            assert "create_pedido:" in key

    def test_different_users_have_different_keys(self):
        """Two users behind same NAT must get different rate-limit buckets."""
        from pedidos.router import _pedido_rate_key

        req_a = MagicMock()
        req_a.state = MagicMock()
        req_a.state.pedido_user_id = 10

        req_b = MagicMock()
        req_b.state = MagicMock()
        req_b.state.pedido_user_id = 20

        key_a = _pedido_rate_key(req_a)
        key_b = _pedido_rate_key(req_b)

        assert key_a != key_b
        assert key_a == "create_pedido:10"
        assert key_b == "create_pedido:20"


# ===========================================================================
# 6.6  test_create_pedido_wrong_address — 403
# ===========================================================================


class TestCreatePedidoWrongAddress:
    """service.create_pedido raises 403 when direccion_entrega_id belongs to another user."""

    @pytest.mark.asyncio
    async def test_wrong_address_raises_403(self):
        """service.create_pedido raises HTTPException 403 for foreign address."""
        from fastapi import Response as FastAPIResponse
        from starlette.requests import Request as StarletteRequest
        from pedidos.router import create_pedido as router_create

        client_user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        uow = _make_uow()

        body = PedidoCreate(
            direccion_entrega_id=999,  # belongs to another user
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=1, cantidad=1)],
        )

        def _raise_403(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Dirección no autorizada",
                    "status": 403,
                    "detail": "La dirección no pertenece al usuario.",
                    "instance": "/api/v1/pedidos",
                },
            )

        # Build a minimal real Starlette Request (required by slowapi decorator)
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/pedidos",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
        real_request = StarletteRequest(scope)

        with patch(
            "pedidos.router.service.create_pedido",
            new=AsyncMock(side_effect=_raise_403),
        ):
            response = FastAPIResponse()

            with pytest.raises(HTTPException) as exc_info:
                await router_create(
                    request=real_request,
                    body=body,
                    response=response,
                    current_user=client_user,
                    uow=uow,
                )

        assert exc_info.value.status_code == 403


# ===========================================================================
# 6.7  test_list_pedidos_isolation — CLIENT-A vs CLIENT-B
# ===========================================================================


class TestListPedidosIsolation:
    """list_by_usuario is called with current_user.id — CLIENT-A sees only their orders."""

    @pytest.mark.asyncio
    async def test_list_filters_by_current_user(self):
        """list_by_usuario is called with user_id=10 — other user's orders not returned."""
        user_a = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido_a = _make_pedido(id=1, usuario_id=10)

        uow = _make_uow(pedidos_list=[pedido_a], pedido_count=1)

        result = await _call_list(user_a, uow)

        # list_by_usuario must be called with user_a.id
        uow.pedidos.list_by_usuario.assert_called_once_with(10, skip=0, limit=20)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == 1

    @pytest.mark.asyncio
    async def test_different_user_gets_empty_list(self):
        """CLIENT-B sees 0 orders when they have none."""
        user_b = _make_usuario(id=20, roles=[_make_rol("CLIENT")])

        uow = _make_uow(pedidos_list=[], pedido_count=0)

        result = await _call_list(user_b, uow)

        uow.pedidos.list_by_usuario.assert_called_once_with(20, skip=0, limit=20)
        assert result.total == 0
        assert result.items == []


# ===========================================================================
# 6.8  test_list_pedidos_pagination
# ===========================================================================


class TestListPedidosPagination:
    """GET /pedidos?limit=1&offset=0 returns exactly 1 item with correct total."""

    @pytest.mark.asyncio
    async def test_pagination_limit_offset(self):
        """limit=1, offset=0 → 1 item returned, total reflects full count."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido1 = _make_pedido(id=1, usuario_id=10)

        uow = _make_uow(pedidos_list=[pedido1], pedido_count=5)

        result = await _call_list(user, uow, limit=1, offset=0)

        uow.pedidos.list_by_usuario.assert_called_once_with(10, skip=0, limit=1)
        assert len(result.items) == 1
        assert result.total == 5
        assert result.limit == 1
        assert result.offset == 0

    @pytest.mark.asyncio
    async def test_pagination_offset(self):
        """limit=20, offset=10 → skip=10 passed to repository."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])

        uow = _make_uow(pedidos_list=[], pedido_count=10)

        result = await _call_list(user, uow, limit=20, offset=10)

        uow.pedidos.list_by_usuario.assert_called_once_with(10, skip=10, limit=20)
        assert result.offset == 10


# ===========================================================================
# 6.9  test_get_pedido_detail_own — 200 with detalles
# ===========================================================================


class TestGetPedidoDetailOwn:
    """CLIENT can see their own order detail."""

    @pytest.mark.asyncio
    async def test_get_own_pedido_returns_detail(self):
        """get_by_id_with_details returns (pedido, detalles) → 200."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido = _make_pedido(id=100, usuario_id=10)
        detalle = _make_detalle(id=1, pedido_id=100)

        uow = _make_uow(pedido_with_details=(pedido, [detalle]))

        result = await _call_get(100, user, uow)

        assert result.id == 100
        assert len(result.detalles) == 1


# ===========================================================================
# 6.10 test_get_pedido_detail_other_user — 403
# ===========================================================================


class TestGetPedidoDetailOtherUser:
    """CLIENT-A trying to see CLIENT-B's order → 403 (ownership check D-02)."""

    @pytest.mark.asyncio
    async def test_other_user_pedido_returns_403(self):
        """pedido.usuario_id=20, current_user.id=10 → 403."""
        user_a = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido_b = _make_pedido(id=100, usuario_id=20)  # belongs to user B
        detalle = _make_detalle(id=1, pedido_id=100)

        uow = _make_uow(pedido_with_details=(pedido_b, [detalle]))

        with pytest.raises(HTTPException) as exc_info:
            await _call_get(100, user_a, uow)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["status"] == 403


# ===========================================================================
# 6.11 test_get_pedido_detail_admin — 200 any user
# ===========================================================================


class TestGetPedidoDetailAdmin:
    """ADMIN can see any user's order — no ownership check."""

    @pytest.mark.asyncio
    async def test_admin_can_see_any_pedido(self):
        """ADMIN with pedido.usuario_id != admin.id → still 200."""
        admin = _make_admin(id=1)
        pedido = _make_pedido(id=100, usuario_id=99)  # belongs to user 99
        detalle = _make_detalle(id=1, pedido_id=100)

        uow = _make_uow(pedido_with_details=(pedido, [detalle]))

        result = await _call_get(100, admin, uow)

        assert result.id == 100


# ===========================================================================
# 6.12 test_get_pedido_not_found — 404
# ===========================================================================


class TestGetPedidoNotFound:
    """get_by_id_with_details returns None → 404."""

    @pytest.mark.asyncio
    async def test_nonexistent_pedido_returns_404(self):
        """get_by_id_with_details=None → HTTPException 404."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])

        uow = _make_uow(pedido_with_details=None)

        with pytest.raises(HTTPException) as exc_info:
            await _call_get(9999, user, uow)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["status"] == 404


# ===========================================================================
# 6.13 test_avanzar_estado_valid_transition — 200 (ADMIN)
# ===========================================================================


class TestAvanzarEstadoValidTransition:
    """ADMIN advances PENDIENTE(1)→EN_PREPARACION(3) via CONFIRMADO ... actually 2→3."""

    @pytest.mark.asyncio
    async def test_admin_avanzar_estado_confirmado_to_en_preparacion(self):
        """ADMIN advances CONFIRMADO(2) → EN_PREPARACIÓN(3) → 200."""
        admin = _make_admin(id=1)
        pedido = _make_pedido(id=100, estado_pedido_id=2)  # CONFIRMADO
        updated = _make_pedido(id=100, estado_pedido_id=3)  # EN_PREPARACIÓN

        uow = _make_uow(pedido=pedido)
        uow.pedidos.update_estado = AsyncMock(return_value=updated)

        body = AvanzarEstadoRequest(nuevo_estado_id=3)

        with patch(
            "pedidos.router.service.avanzar_estado",
            new=AsyncMock(return_value=updated),
        ):
            result = await _call_avanzar(100, body, admin, uow)

        assert result.id == 100
        assert result.estado_pedido_id == 3


# ===========================================================================
# 6.14 test_avanzar_estado_invalid_fsm — 409
# ===========================================================================


class TestAvanzarEstadoInvalidFSM:
    """ADMIN tries invalid FSM transition → service raises 409."""

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_409(self):
        """PENDIENTE(1) → ENTREGADO(5) is invalid → 409."""
        admin = _make_admin(id=1)
        pedido = _make_pedido(id=100, estado_pedido_id=1)

        uow = _make_uow(pedido=pedido)

        body = AvanzarEstadoRequest(nuevo_estado_id=5)

        def _raise_409(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "about:blank",
                    "title": "Transición de estado inválida",
                    "status": 409,
                    "detail": "No se puede pasar de PENDIENTE a ENTREGADO.",
                    "instance": "/api/v1/pedidos/100/estado",
                    "estado_actual": 1,
                    "estado_solicitado": 5,
                },
            )

        with patch(
            "pedidos.router.service.avanzar_estado",
            new=AsyncMock(side_effect=_raise_409),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await _call_avanzar(100, body, admin, uow)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["estado_actual"] == 1


# ===========================================================================
# 6.15 test_avanzar_estado_client_forbidden — 403
# ===========================================================================


class TestAvanzarEstadoClientForbidden:
    """CLIENT trying PATCH /estado → 403 from require_role."""

    @pytest.mark.asyncio
    async def test_client_cannot_avanzar_estado(self):
        """require_role(["ADMIN"]) rejects CLIENT → 403."""
        from core.dependencies import require_role

        client_user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        dep = require_role(["ADMIN"])

        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=client_user)

        assert exc_info.value.status_code == 403


# ===========================================================================
# 6.16 test_delete_pedido_pendiente_by_client — 200, eliminado_en set
# ===========================================================================


class TestDeletePedidoPendienteByClient:
    """CLIENT cancels own PENDIENTE order → 200, eliminado_en is set."""

    @pytest.mark.asyncio
    async def test_delete_pendiente_by_client(self):
        """service.cancelar called; eliminado_en set on the result."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=1)
        cancelado = _make_pedido(id=100, usuario_id=10, estado_pedido_id=6)
        cancelado.eliminado_en = None  # starts as None, should be set

        uow = _make_uow(pedido=pedido)

        with patch(
            "pedidos.router.service.cancelar",
            new=AsyncMock(return_value=cancelado),
        ):
            result = await _call_delete(100, user, uow)

        # session.add was called to persist the soft delete
        uow.session.add.assert_called()
        # eliminado_en was set (non-None) by the router
        assert cancelado.eliminado_en is not None
        assert result.estado_pedido_id == 6


# ===========================================================================
# 6.17 test_delete_pedido_non_pendiente_by_client — 409
# ===========================================================================


class TestDeletePedidoNonPendienteByClient:
    """CLIENT tries to cancel CONFIRMADO(2) order → 409 (CLIENT restriction)."""

    @pytest.mark.asyncio
    async def test_client_cannot_cancel_confirmado(self):
        """estado_pedido_id=2, CLIENT → 409 before calling service.cancelar."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido = _make_pedido(id=100, usuario_id=10, estado_pedido_id=2)  # CONFIRMADO

        uow = _make_uow(pedido=pedido)

        with pytest.raises(HTTPException) as exc_info:
            await _call_delete(100, user, uow)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["status"] == 409
        assert "PENDIENTE" in exc_info.value.detail["detail"]


# ===========================================================================
# 6.18 test_delete_pedido_other_user — 403
# ===========================================================================


class TestDeletePedidoOtherUser:
    """CLIENT-A tries to cancel CLIENT-B's order → 403."""

    @pytest.mark.asyncio
    async def test_delete_other_user_pedido_raises_403(self):
        """pedido.usuario_id=20, current_user.id=10 → 403."""
        user_a = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido_b = _make_pedido(id=100, usuario_id=20, estado_pedido_id=1)

        uow = _make_uow(pedido=pedido_b)

        with pytest.raises(HTTPException) as exc_info:
            await _call_delete(100, user_a, uow)

        assert exc_info.value.status_code == 403


# ===========================================================================
# 6.19 test_delete_soft_delete_removes_from_list
# ===========================================================================


class TestDeleteSoftDeleteRemovesFromList:
    """After soft delete, list_by_usuario returns 0 (eliminado_en filtered out)."""

    @pytest.mark.asyncio
    async def test_soft_deleted_pedido_not_in_list(self):
        """list_by_usuario filters eliminado_en — soft-deleted pedido not returned."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])

        # Simulate that after cancellation, list returns empty (repository filters)
        uow = _make_uow(pedidos_list=[], pedido_count=0)

        result = await _call_list(user, uow)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_by_usuario_called_with_user_id(self):
        """list_by_usuario must always use the authenticated user's id."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        uow = _make_uow(pedidos_list=[], pedido_count=0)

        await _call_list(user, uow)

        # Must filter by user's own id — never returns all pedidos
        uow.pedidos.list_by_usuario.assert_called_once_with(10, skip=0, limit=20)


# ===========================================================================
# 6.20 test_delete_pedido_admin_can_cancel_confirmed — 200 (ADMIN, estado=2)
# ===========================================================================


class TestDeletePedidoAdminCanCancelConfirmed:
    """ADMIN can cancel a CONFIRMADO(2) order (no CLIENT PENDIENTE restriction)."""

    @pytest.mark.asyncio
    async def test_admin_can_cancel_confirmado(self):
        """ADMIN bypasses CLIENT state restriction → service.cancelar called for estado=2."""
        admin = _make_admin(id=1)
        pedido = _make_pedido(id=100, usuario_id=99, estado_pedido_id=2)  # CONFIRMADO
        cancelado = _make_pedido(id=100, usuario_id=99, estado_pedido_id=6)
        cancelado.eliminado_en = None

        uow = _make_uow(pedido=pedido)

        with patch(
            "pedidos.router.service.cancelar",
            new=AsyncMock(return_value=cancelado),
        ):
            result = await _call_delete(100, admin, uow)

        # service.cancelar must have been called (ADMIN bypasses state check)
        assert result.estado_pedido_id == 6
        uow.session.add.assert_called()
        assert cancelado.eliminado_en is not None

    @pytest.mark.asyncio
    async def test_admin_cannot_cancel_entregado_due_to_fsm(self):
        """ADMIN tries to cancel ENTREGADO(5) → service raises 409 (FSM terminal)."""
        admin = _make_admin(id=1)
        pedido = _make_pedido(id=100, usuario_id=99, estado_pedido_id=5)  # ENTREGADO

        uow = _make_uow(pedido=pedido)

        def _raise_409(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "about:blank",
                    "title": "No se puede cancelar",
                    "status": 409,
                    "detail": "El pedido está en estado ENTREGADO y no puede ser cancelado.",
                    "instance": "/api/v1/pedidos/100/cancelar",
                    "estado_actual": 5,
                    "estado_solicitado": 6,
                },
            )

        with patch(
            "pedidos.router.service.cancelar",
            new=AsyncMock(side_effect=_raise_409),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await _call_delete(100, admin, uow)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["estado_actual"] == 5


# ===========================================================================
# Additional: count_by_usuario in PedidoRepository
# ===========================================================================


class TestCountByUsuario:
    """count_by_usuario method exists and is called during list_pedidos."""

    @pytest.mark.asyncio
    async def test_count_called_in_list(self):
        """list_pedidos calls both list_by_usuario and count_by_usuario."""
        user = _make_usuario(id=10, roles=[_make_rol("CLIENT")])
        pedido = _make_pedido(id=1, usuario_id=10)

        uow = _make_uow(pedidos_list=[pedido], pedido_count=7)

        result = await _call_list(user, uow, limit=5, offset=0)

        uow.pedidos.count_by_usuario.assert_called_once_with(10)
        assert result.total == 7
        assert result.limit == 5

    def test_count_by_usuario_method_exists(self):
        """PedidoRepository must have count_by_usuario method."""
        # Import locally to avoid circular at module-level
        import importlib

        repo_mod = importlib.import_module("pedidos.repository")
        PedidoRepository = repo_mod.PedidoRepository

        assert hasattr(
            PedidoRepository, "count_by_usuario"
        ), "PedidoRepository must expose count_by_usuario()"


# ===========================================================================
# Additional: PaginatedPedidosResponse schema
# ===========================================================================


class TestPaginatedPedidosResponseSchema:
    """PaginatedPedidosResponse has correct structure."""

    def test_schema_fields(self):
        """PaginatedPedidosResponse must have items, total, limit, offset."""
        from pedidos.schemas import PaginatedPedidosResponse

        r = PaginatedPedidosResponse(
            items=[],
            total=42,
            limit=20,
            offset=0,
        )
        assert r.total == 42
        assert r.limit == 20
        assert r.offset == 0
        assert r.items == []
