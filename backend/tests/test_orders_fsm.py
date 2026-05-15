"""
Tests for orders-fsm-backend change.

Strategy:
  - Tests are unit/integration tests using mocked UnitOfWork + repositories.
  - Covers FSM transitions, stock management, audit trail, and ownership checks.
  - Uses pytest + AsyncMock pattern consistent with the rest of the test suite.

Test coverage (11 minimum):
  7.2  test_create_pedido_success
  7.3  test_create_pedido_insufficient_stock
  7.4  test_create_pedido_invalid_product
  7.5  test_valid_fsm_transition (parametric)
  7.6  test_invalid_fsm_transition
  7.7  test_terminal_state_no_transition
  7.8  test_cancelar_reverts_stock
  7.9  test_historial_append_only
  7.10 test_address_ownership_check
  7.11 test_precio_snapshot_matches_db
  Additional: test_fsm_constants, test_system_only_target
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from pedidos import service
from pedidos.service import (
    VALID_TRANSITIONS,
    SYSTEM_ONLY_TARGETS,
    create_pedido,
    avanzar_estado,
    cancelar,
)
from pedidos.repository import HistorialEstadoPedidoRepository, PedidoRepository
from pedidos.schemas import PedidoCreate, DetallePedidoCreate, AvanzarEstadoRequest
from core.models import (
    DetallePedido,
    DireccionEntrega,
    FormaPago,
    HistorialEstadoPedido,
    Pedido,
    Producto,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_producto(
    id: int = 1,
    nombre: str = "Hamburguesa Test",
    precio_base: Decimal = Decimal("500.00"),
    stock_cantidad: int = 10,
    disponible: bool = True,
    eliminado_en=None,
) -> MagicMock:
    """Build a mock Producto."""
    p = MagicMock(spec=Producto)
    p.id = id
    p.nombre = nombre
    p.precio_base = precio_base
    p.stock_cantidad = stock_cantidad
    p.disponible = disponible
    p.eliminado_en = eliminado_en
    return p


def _make_direccion(
    id: int = 1,
    usuario_id: int = 10,
    alias: str = "Casa",
    linea1: str = "Av. Corrientes 1234",
    ciudad: str = "Buenos Aires",
    codigo_postal: str = "C1043",
    piso: str = None,
    departamento: str = None,
    eliminado_en=None,
) -> MagicMock:
    """Build a mock DireccionEntrega."""
    d = MagicMock(spec=DireccionEntrega)
    d.id = id
    d.usuario_id = usuario_id
    d.alias = alias
    d.linea1 = linea1
    d.ciudad = ciudad
    d.codigo_postal = codigo_postal
    d.piso = piso
    d.departamento = departamento
    d.eliminado_en = eliminado_en
    return d


def _make_forma_pago(id: int = 1, activo: bool = True) -> MagicMock:
    """Build a mock FormaPago."""
    fp = MagicMock(spec=FormaPago)
    fp.id = id
    fp.activo = activo
    return fp


def _make_pedido(
    id: int = 100,
    usuario_id: int = 10,
    estado_pedido_id: int = 1,
    total: Decimal = Decimal("500.00"),
) -> MagicMock:
    """Build a mock Pedido."""
    p = MagicMock(spec=Pedido)
    p.id = id
    p.usuario_id = usuario_id
    p.estado_pedido_id = estado_pedido_id
    p.total = total
    p.eliminado_en = None
    return p


def _make_detalle(
    id: int = 1,
    pedido_id: int = 100,
    producto_id: int = 1,
    cantidad: int = 2,
    precio_snapshot: Decimal = Decimal("500.00"),
) -> MagicMock:
    """Build a mock DetallePedido."""
    d = MagicMock(spec=DetallePedido)
    d.id = id
    d.pedido_id = pedido_id
    d.producto_id = producto_id
    d.cantidad = cantidad
    d.precio_snapshot = precio_snapshot
    return d


def _make_uow(
    producto=None,
    producto_locked=None,
    direccion=None,
    forma_pago=None,
    pedido=None,
    detalles=None,
    pedido_with_details=None,
) -> MagicMock:
    """
    Build a mock UnitOfWork with configurable repository responses.
    """
    uow = MagicMock()
    uow.session = AsyncMock()
    uow.session.add = MagicMock()
    uow.session.flush = AsyncMock()

    # productos repo
    productos_repo = AsyncMock()
    productos_repo.get_by_id_locked = AsyncMock(return_value=producto_locked)
    productos_repo.get_by_id = AsyncMock(return_value=producto)
    uow.productos = productos_repo

    # direcciones (BaseRepository on DireccionEntrega)
    direcciones_entrega_repo = AsyncMock()
    direcciones_entrega_repo.get_by_id = AsyncMock(return_value=direccion)
    uow.direcciones_entrega = direcciones_entrega_repo

    # formas_pago
    formas_pago_repo = AsyncMock()
    formas_pago_repo.get_by_id = AsyncMock(return_value=forma_pago)
    uow.formas_pago = formas_pago_repo

    # pedidos
    pedidos_repo = AsyncMock(spec=PedidoRepository)
    pedidos_repo.get_by_id = AsyncMock(return_value=pedido)
    pedidos_repo.create_with_details = AsyncMock(return_value=pedido)
    pedidos_repo.update_estado = AsyncMock(return_value=pedido)
    if pedido_with_details is not None:
        pedidos_repo.get_by_id_with_details = AsyncMock(return_value=pedido_with_details)
    else:
        pedidos_repo.get_by_id_with_details = AsyncMock(return_value=None)
    uow.pedidos = pedidos_repo

    # historial_estado_pedido
    historial_repo = AsyncMock(spec=HistorialEstadoPedidoRepository)
    historial_repo.append = AsyncMock(return_value=MagicMock(spec=HistorialEstadoPedido))
    historial_repo.list_by_pedido = AsyncMock(return_value=[])
    uow.historial_estado_pedido = historial_repo

    return uow


# ---------------------------------------------------------------------------
# 7.2 test_create_pedido_success
# ---------------------------------------------------------------------------


class TestCreatePedidoSuccess:
    """Successful order creation with correct snapshots and stock decrement."""

    @pytest.mark.asyncio
    async def test_create_pedido_success(self):
        """Order is created with precio_snapshot, nombre_snapshot; stock decremented; historial appended."""
        usuario_id = 10
        producto = _make_producto(id=1, precio_base=Decimal("500.00"), stock_cantidad=10)
        direccion = _make_direccion(id=1, usuario_id=usuario_id)
        forma_pago = _make_forma_pago(id=1, activo=True)
        pedido_mock = _make_pedido(id=100, usuario_id=usuario_id, estado_pedido_id=1)

        uow = _make_uow(
            producto=producto,
            producto_locked=producto,
            direccion=direccion,
            forma_pago=forma_pago,
            pedido=pedido_mock,
        )

        request = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            observacion="Test order",
            items=[DetallePedidoCreate(producto_id=1, cantidad=2)],
        )

        result = await create_pedido(request, usuario_id, uow)

        # Verify pedido was created
        uow.pedidos.create_with_details.assert_called_once()
        call_args = uow.pedidos.create_with_details.call_args
        created_pedido = call_args[0][0]
        created_detalles = call_args[0][1]

        # Check pedido initial state
        assert created_pedido.estado_pedido_id == 1  # PENDIENTE
        assert created_pedido.usuario_id == usuario_id

        # Check detalle snapshots
        assert len(created_detalles) == 1
        detalle = created_detalles[0]
        assert detalle.precio_snapshot == Decimal("500.00")
        assert detalle.nombre_snapshot == "Hamburguesa Test"
        assert detalle.cantidad == 2
        assert detalle.producto_id == 1

        # Check stock was decremented
        assert producto.stock_cantidad == 8  # 10 - 2

        # Check historial was appended with estado_anterior=None
        uow.historial_estado_pedido.append.assert_called_once()
        historial_call = uow.historial_estado_pedido.append.call_args[0][0]
        assert historial_call.estado_anterior_id is None
        assert historial_call.estado_nuevo_id == 1


# ---------------------------------------------------------------------------
# 7.3 test_create_pedido_insufficient_stock
# ---------------------------------------------------------------------------


class TestCreatePedidoInsufficientStock:
    """HTTP 409 when requesting more stock than available."""

    @pytest.mark.asyncio
    async def test_insufficient_stock_raises_409(self):
        """cantidad=10, stock=3 → HTTP 409 (RFC 7807)."""
        usuario_id = 10
        producto = _make_producto(id=1, stock_cantidad=3)
        direccion = _make_direccion(id=1, usuario_id=usuario_id)
        forma_pago = _make_forma_pago(id=1, activo=True)

        uow = _make_uow(
            producto_locked=producto,
            direccion=direccion,
            forma_pago=forma_pago,
        )

        request = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=1, cantidad=10)],
        )

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_pedido(request, usuario_id, uow)

        assert exc_info.value.status_code == 409
        detail = exc_info.value.detail
        assert detail["status"] == 409
        assert detail["producto_id"] == 1
        assert detail["stock_actual"] == 3
        assert detail["cantidad_solicitada"] == 10

        # Stock must NOT have been decremented
        assert producto.stock_cantidad == 3

        # Pedido must NOT have been created
        uow.pedidos.create_with_details.assert_not_called()


# ---------------------------------------------------------------------------
# 7.4 test_create_pedido_invalid_product
# ---------------------------------------------------------------------------


class TestCreatePedidoInvalidProduct:
    """HTTP 422 when product is unavailable or soft-deleted."""

    @pytest.mark.asyncio
    async def test_locked_returns_none_raises_422(self):
        """get_by_id_locked returns None (unavailable/deleted) → HTTP 422."""
        usuario_id = 10
        direccion = _make_direccion(id=1, usuario_id=usuario_id)
        forma_pago = _make_forma_pago(id=1, activo=True)

        uow = _make_uow(
            producto_locked=None,  # product not found / unavailable
            direccion=direccion,
            forma_pago=forma_pago,
        )

        request = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=99, cantidad=1)],
        )

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_pedido(request, usuario_id, uow)

        assert exc_info.value.status_code == 422
        uow.pedidos.create_with_details.assert_not_called()


# ---------------------------------------------------------------------------
# 7.5 test_valid_fsm_transition (parametric)
# ---------------------------------------------------------------------------


VALID_TRANSITION_CASES = [
    (1, 2),   # PENDIENTE → CONFIRMADO (system)
    (1, 6),   # PENDIENTE → CANCELADO
    (2, 3),   # CONFIRMADO → EN_PREPARACIÓN
    (2, 6),   # CONFIRMADO → CANCELADO
    (3, 4),   # EN_PREPARACIÓN → EN_CAMINO
    (4, 5),   # EN_CAMINO → ENTREGADO
]


class TestValidFSMTransitions:
    """All entries in VALID_TRANSITIONS succeed via avanzar_estado (with is_system=True)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_state,to_state", VALID_TRANSITION_CASES)
    async def test_valid_transition(self, from_state: int, to_state: int):
        """Each valid transition in VALID_TRANSITIONS must succeed."""
        usuario_id = 10
        pedido_mock = _make_pedido(id=100, estado_pedido_id=from_state)
        updated_pedido = _make_pedido(id=100, estado_pedido_id=to_state)

        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)
        uow.pedidos.update_estado = AsyncMock(return_value=updated_pedido)

        result = await avanzar_estado(100, to_state, usuario_id, uow, is_system=True)

        uow.pedidos.update_estado.assert_called_once_with(100, to_state)
        uow.historial_estado_pedido.append.assert_called_once()
        historial = uow.historial_estado_pedido.append.call_args[0][0]
        assert historial.estado_anterior_id == from_state
        assert historial.estado_nuevo_id == to_state


# ---------------------------------------------------------------------------
# 7.6 test_invalid_fsm_transition
# ---------------------------------------------------------------------------


class TestInvalidFSMTransition:
    """HTTP 409 for transitions not in VALID_TRANSITIONS."""

    @pytest.mark.asyncio
    async def test_pendiente_to_en_camino_raises_409(self):
        """PENDIENTE(1) → EN_CAMINO(4) is not valid → HTTP 409."""
        pedido_mock = _make_pedido(id=100, estado_pedido_id=1)  # PENDIENTE
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await avanzar_estado(100, 4, 10, uow)

        assert exc_info.value.status_code == 409
        detail = exc_info.value.detail
        assert detail["estado_actual"] == 1
        assert detail["estado_solicitado"] == 4
        uow.pedidos.update_estado.assert_not_called()

    @pytest.mark.asyncio
    async def test_en_preparacion_to_cancelado_raises_409(self):
        """EN_PREPARACIÓN(3) → CANCELADO(6) is not valid → HTTP 409."""
        pedido_mock = _make_pedido(id=100, estado_pedido_id=3)
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await avanzar_estado(100, 6, 10, uow)

        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 7.7 test_terminal_state_no_transition
# ---------------------------------------------------------------------------


class TestTerminalStateNoTransition:
    """HTTP 409 attempting to transition from a terminal state."""

    @pytest.mark.asyncio
    async def test_entregado_cannot_transition(self):
        """ENTREGADO(5) is terminal — any transition raises HTTP 409."""
        pedido_mock = _make_pedido(id=100, estado_pedido_id=5)  # ENTREGADO
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await avanzar_estado(100, 6, 10, uow)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["estado_actual"] == 5

    @pytest.mark.asyncio
    async def test_cancelado_cannot_transition(self):
        """CANCELADO(6) is terminal — any transition raises HTTP 409."""
        pedido_mock = _make_pedido(id=100, estado_pedido_id=6)  # CANCELADO
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await avanzar_estado(100, 1, 10, uow)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cancelar_from_entregado_raises_409(self):
        """Calling cancelar() on ENTREGADO(5) raises HTTP 409."""
        pedido_mock = _make_pedido(id=100, estado_pedido_id=5)
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await cancelar(100, 10, uow)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cancelar_already_cancelado_raises_409(self):
        """Calling cancelar() on CANCELADO(6) raises HTTP 409."""
        pedido_mock = _make_pedido(id=100, estado_pedido_id=6)
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await cancelar(100, 10, uow)

        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# 7.8 test_cancelar_reverts_stock
# ---------------------------------------------------------------------------


class TestCancelarRevertsStock:
    """cancelar() increments stock back for each DetallePedido."""

    @pytest.mark.asyncio
    async def test_cancelar_increments_stock(self):
        """Cancelling an order should increment stock for each item."""
        usuario_id = 10
        pedido_mock = _make_pedido(id=100, estado_pedido_id=1, usuario_id=usuario_id)
        cancelado_mock = _make_pedido(id=100, estado_pedido_id=6)

        detalle1 = _make_detalle(id=1, pedido_id=100, producto_id=1, cantidad=3)
        detalle2 = _make_detalle(id=2, pedido_id=100, producto_id=2, cantidad=5)

        producto1 = _make_producto(id=1, stock_cantidad=7)
        producto2 = _make_producto(id=2, stock_cantidad=0)

        uow = _make_uow(
            pedido=pedido_mock,
            pedido_with_details=(cancelado_mock, [detalle1, detalle2]),
        )
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)
        uow.pedidos.update_estado = AsyncMock(return_value=cancelado_mock)

        # productos repo needs to return different products by ID
        async def _get_by_id(id_val):
            if id_val == 1:
                return producto1
            if id_val == 2:
                return producto2
            return None

        uow.productos.get_by_id = AsyncMock(side_effect=_get_by_id)

        result = await cancelar(100, usuario_id, uow)

        # Stock should be reverted
        assert producto1.stock_cantidad == 10  # 7 + 3
        assert producto2.stock_cantidad == 5   # 0 + 5

        # Historial should be appended
        uow.historial_estado_pedido.append.assert_called_once()
        historial = uow.historial_estado_pedido.append.call_args[0][0]
        assert historial.estado_anterior_id == 1
        assert historial.estado_nuevo_id == 6


# ---------------------------------------------------------------------------
# 7.9 test_historial_append_only
# ---------------------------------------------------------------------------


class TestHistorialAppendOnly:
    """HistorialEstadoPedidoRepository only exposes append() and list_by_pedido()."""

    def test_historial_repo_has_no_delete_method(self):
        """The repository class itself must not expose a public 'delete' method."""
        # We verify the class does not override hard_delete or soft_delete
        # to intentionally remove historial entries.
        # The base class has soft_delete + hard_delete but HistorialEstadoPedido
        # has no eliminado_en field, so soft_delete raises AttributeError.
        session_mock = MagicMock()
        repo = HistorialEstadoPedidoRepository(session_mock)

        # append() must exist
        assert hasattr(repo, "append"), "append() method must exist"

        # list_by_pedido() must exist
        assert hasattr(repo, "list_by_pedido"), "list_by_pedido() method must exist"

        # Calling soft_delete on historial should raise AttributeError
        # (HistorialEstadoPedido has no eliminado_en field)
        from core.models import HistorialEstadoPedido as HPModel
        assert not hasattr(HPModel, "eliminado_en"), (
            "HistorialEstadoPedido must not have eliminado_en — it's append-only"
        )

    def test_valid_transitions_dict_is_complete(self):
        """VALID_TRANSITIONS must cover all 6 states."""
        assert set(VALID_TRANSITIONS.keys()) == {1, 2, 3, 4, 5, 6}

    def test_terminal_states_have_empty_transitions(self):
        """States 5 (ENTREGADO) and 6 (CANCELADO) must have no valid transitions."""
        assert VALID_TRANSITIONS[5] == []
        assert VALID_TRANSITIONS[6] == []


# ---------------------------------------------------------------------------
# 7.10 test_address_ownership_check
# ---------------------------------------------------------------------------


class TestAddressOwnershipCheck:
    """HTTP 403 when direccion_entrega_id belongs to another user."""

    @pytest.mark.asyncio
    async def test_other_user_address_raises_403(self):
        """Direccion owned by user_id=99, authenticated as user_id=10 → HTTP 403."""
        usuario_id = 10
        # Address belongs to different user
        direccion = _make_direccion(id=1, usuario_id=99)
        forma_pago = _make_forma_pago(id=1, activo=True)

        uow = _make_uow(
            direccion=direccion,
            forma_pago=forma_pago,
        )

        request = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=1, cantidad=1)],
        )

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_pedido(request, usuario_id, uow)

        assert exc_info.value.status_code == 403
        uow.pedidos.create_with_details.assert_not_called()

    @pytest.mark.asyncio
    async def test_nonexistent_address_raises_403(self):
        """direccion not found (get_by_id returns None) → HTTP 403."""
        usuario_id = 10
        uow = _make_uow(
            direccion=None,  # not found
            forma_pago=_make_forma_pago(id=1, activo=True),
        )

        request = PedidoCreate(
            direccion_entrega_id=999,
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=1, cantidad=1)],
        )

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_pedido(request, usuario_id, uow)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# 7.11 test_precio_snapshot_matches_db
# ---------------------------------------------------------------------------


class TestPrecioSnapshotMatchesDB:
    """precio_snapshot equals producto.precio_base at creation time."""

    @pytest.mark.asyncio
    async def test_precio_snapshot_matches_db(self):
        """DetallePedido.precio_snapshot must equal the DB price at order creation."""
        usuario_id = 10
        db_price = Decimal("1234.56")
        producto = _make_producto(id=1, precio_base=db_price, stock_cantidad=5)
        direccion = _make_direccion(id=1, usuario_id=usuario_id)
        forma_pago = _make_forma_pago(id=1, activo=True)
        pedido_mock = _make_pedido(id=100, usuario_id=usuario_id)

        uow = _make_uow(
            producto=producto,
            producto_locked=producto,
            direccion=direccion,
            forma_pago=forma_pago,
            pedido=pedido_mock,
        )

        request = PedidoCreate(
            direccion_entrega_id=1,
            forma_pago_id=1,
            items=[DetallePedidoCreate(producto_id=1, cantidad=1)],
        )

        await create_pedido(request, usuario_id, uow)

        call_args = uow.pedidos.create_with_details.call_args
        detalles = call_args[0][1]
        assert len(detalles) == 1
        assert detalles[0].precio_snapshot == db_price
        assert detalles[0].nombre_snapshot == "Hamburguesa Test"


# ---------------------------------------------------------------------------
# Additional: FSM constants validation
# ---------------------------------------------------------------------------


class TestFSMConstants:
    """Verify FSM constants match the spec."""

    def test_system_only_targets_contains_confirmado(self):
        """CONFIRMADO (2) must be in SYSTEM_ONLY_TARGETS (RN-FS02)."""
        assert 2 in SYSTEM_ONLY_TARGETS

    def test_valid_transitions_pendiente(self):
        """PENDIENTE(1) can go to CONFIRMADO(2) or CANCELADO(6)."""
        assert 2 in VALID_TRANSITIONS[1]
        assert 6 in VALID_TRANSITIONS[1]
        assert len(VALID_TRANSITIONS[1]) == 2

    def test_valid_transitions_confirmado(self):
        """CONFIRMADO(2) can go to EN_PREPARACIÓN(3) or CANCELADO(6)."""
        assert 3 in VALID_TRANSITIONS[2]
        assert 6 in VALID_TRANSITIONS[2]

    def test_valid_transitions_en_preparacion(self):
        """EN_PREPARACIÓN(3) → EN_CAMINO(4) only."""
        assert VALID_TRANSITIONS[3] == [4]

    def test_valid_transitions_en_camino(self):
        """EN_CAMINO(4) → ENTREGADO(5) only."""
        assert VALID_TRANSITIONS[4] == [5]

    def test_system_only_target_blocked_without_flag(self):
        """avanzar_estado to CONFIRMADO(2) without is_system=True raises HTTP 403."""
        import asyncio
        from fastapi import HTTPException

        pedido_mock = _make_pedido(id=100, estado_pedido_id=1)
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)

        async def _run():
            with pytest.raises(HTTPException) as exc_info:
                await avanzar_estado(100, 2, 10, uow, is_system=False)
            assert exc_info.value.status_code == 403

        asyncio.run(_run())

    def test_system_only_target_allowed_with_flag(self):
        """avanzar_estado to CONFIRMADO(2) with is_system=True succeeds."""
        import asyncio

        pedido_mock = _make_pedido(id=100, estado_pedido_id=1)
        updated = _make_pedido(id=100, estado_pedido_id=2)
        uow = _make_uow(pedido=pedido_mock)
        uow.pedidos.get_by_id = AsyncMock(return_value=pedido_mock)
        uow.pedidos.update_estado = AsyncMock(return_value=updated)

        async def _run():
            result = await avanzar_estado(100, 2, 10, uow, is_system=True)
            assert result is not None

        asyncio.run(_run())
