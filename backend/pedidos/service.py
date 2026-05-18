"""
PedidosService — business logic for order-related operations.

Operations:
  - validar_carrito(): Pre-checkout validation. Read-only advisory check that
    detects empty cart, missing address, insufficient stock, and price drift.
    Returns a structured ValidarCarritoResponse without mutating any DB state.

  - create_pedido(): Create a new order with stock decrement, snapshots, and
    FSM initial state (PENDIENTE). Uses SELECT FOR UPDATE to prevent race
    conditions (RN-PE04).

  - avanzar_estado(): Transition a pedido through FSM states following the
    VALID_TRANSITIONS matrix (D-03). Raises HTTP 409 for invalid transitions.

  - cancelar(): Cancel an order (state → CANCELADO=6) and revert all stock.

Architecture:
  Router → Service → UoW → Repository → Model
  - Service raises HTTPException — never router, never repository.
  - Service NEVER calls session.commit() directly — UoW manages the lifecycle.

FSM States (seedeados en DB — NO modificar tabla estados_pedido):
  1=PENDIENTE, 2=CONFIRMADO, 3=EN_PREPARACIÓN, 4=EN_CAMINO,
  5=ENTREGADO, 6=CANCELADO

Valid transitions:
  1→2 (System only), 1→6, 2→3, 2→6 (ADMIN only), 3→4, 4→5
  5 and 6 are terminal states — no transitions from them.
"""
import json
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status

from core.models import DetallePedido, HistorialEstadoPedido, Pedido
from infrastructure.uow import UnitOfWork
from pedidos.schemas import (
    CambioPrecioItem,
    PedidoCreate,
    StockInsuficienteItem,
    ValidarCarritoRequest,
    ValidarCarritoResponse,
)

# ---------------------------------------------------------------------------
# FSM constants (D-03)
# ---------------------------------------------------------------------------

# All valid state transitions: {current_estado_id: [allowed_next_estado_ids]}
VALID_TRANSITIONS: dict[int, list[int]] = {
    1: [2, 6],  # PENDIENTE → CONFIRMADO (system only) | CANCELADO
    2: [3, 6],  # CONFIRMADO → EN_PREPARACIÓN | CANCELADO (ADMIN only)
    3: [4],  # EN_PREPARACIÓN → EN_CAMINO
    4: [5],  # EN_CAMINO → ENTREGADO
    5: [],  # ENTREGADO — terminal, no transitions
    6: [],  # CANCELADO — terminal, no transitions
}

# States that can only be the TARGET of a system/webhook transition (RN-FS02)
# CLIENT cannot manually request transition TO CONFIRMADO
SYSTEM_ONLY_TARGETS: set[int] = {2}

# Human-readable state names for error messages
_ESTADO_NOMBRES: dict[int, str] = {
    1: "PENDIENTE",
    2: "CONFIRMADO",
    3: "EN_PREPARACIÓN",
    4: "EN_CAMINO",
    5: "ENTREGADO",
    6: "CANCELADO",
}


async def validar_carrito(
    request: ValidarCarritoRequest,
    usuario_id: int,
    uow: UnitOfWork,
) -> ValidarCarritoResponse:
    """
    Pre-checkout cart validation (read-only).

    Performs four checks in sequence:
      1. Hard block: empty cart (items list has zero elements).
      2. Hard block: user has no active delivery addresses.
      3. Soft warning: stock insufficient for one or more items.
      4. Soft warning: cart-stored price drifted from current DB price (> 0.01).

    Hard blocks raise HTTP 422 (RFC 7807) immediately and never proceed to
    product lookup. Soft warnings accumulate in the response body and return
    HTTP 200 so the frontend can surface them to the user.

    The service NEVER mutates the database — it is advisory only.
    Stock is NOT reserved here; actual reservation happens at order creation.

    Args:
        request: Validated cart payload (items + direccion_id).
        usuario_id: Authenticated user's primary key.
        uow: Injected UnitOfWork (session already open, no commit triggered).

    Returns:
        ValidarCarritoResponse with populated warning lists.

    Raises:
        HTTPException 422: If cart is empty OR user has no active addresses.
    """
    # ------------------------------------------------------------------
    # 3.2 — Hard block: empty cart
    # ------------------------------------------------------------------
    if len(request.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Carrito vacío",
                "status": 422,
                "detail": "El carrito no puede estar vacío para iniciar el checkout.",
                "instance": "/api/v1/pedidos/validar",
            },
        )

    # ------------------------------------------------------------------
    # 3.3 — Hard block: user has no active delivery address
    # ------------------------------------------------------------------
    address_count = await uow.direcciones.count_active_by_usuario(usuario_id)
    if address_count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Sin dirección de entrega",
                "status": 422,
                "detail": "El usuario no tiene ninguna dirección de entrega activa. "
                "Por favor agregá una dirección antes de continuar.",
                "instance": "/api/v1/pedidos/validar",
            },
        )

    # ------------------------------------------------------------------
    # 3.4 — Batch product lookup (single IN query — D-02)
    # ------------------------------------------------------------------
    producto_ids = [item.producto_id for item in request.items]
    productos = await uow.productos.get_by_ids(producto_ids)

    # ------------------------------------------------------------------
    # 3.5 — Build O(1) lookup map
    # ------------------------------------------------------------------
    productos_map = {p.id: p for p in productos}

    # ------------------------------------------------------------------
    # 3.6–3.9 — Iterate items and classify issues
    # ------------------------------------------------------------------
    stock_insuficiente: list[StockInsuficienteItem] = []
    productos_invalidos: list[int] = []
    cambios_de_precio: list[CambioPrecioItem] = []

    for item in request.items:
        producto = productos_map.get(item.producto_id)

        # 3.6 — Product not found in DB
        if producto is None:
            productos_invalidos.append(item.producto_id)
            continue

        # 3.7 — Product exists but is unavailable or soft-deleted
        if not producto.disponible or producto.eliminado_en is not None:
            productos_invalidos.append(item.producto_id)
            continue

        # Product is valid — check stock and price
        # 3.8 — Insufficient stock
        if item.cantidad > producto.stock_cantidad:
            stock_insuficiente.append(
                StockInsuficienteItem(
                    producto_id=producto.id,
                    nombre=producto.nombre,
                    stock_actual=producto.stock_cantidad,
                    cantidad_solicitada=item.cantidad,
                )
            )

        # 3.9 — Price drift (tolerance: 1 centavo — D-04)
        if abs(item.precio_carrito - producto.precio_base) > Decimal("0.01"):
            cambios_de_precio.append(
                CambioPrecioItem(
                    producto_id=producto.id,
                    precio_carrito=item.precio_carrito,
                    precio_actual=producto.precio_base,
                )
            )

    # ------------------------------------------------------------------
    # 3.10 — Build and return the structured response
    # ------------------------------------------------------------------
    return ValidarCarritoResponse(
        stock_insuficiente=stock_insuficiente,
        productos_invalidos=productos_invalidos,
        cambios_de_precio=cambios_de_precio,
        carrito_vacio=False,
        sin_direccion=False,
    )


# ---------------------------------------------------------------------------
# create_pedido — Task 4.3
# ---------------------------------------------------------------------------


async def create_pedido(
    request: PedidoCreate,
    usuario_id: int,
    uow: UnitOfWork,
) -> Pedido:
    """
    Create a new order with stock decrement and audit trail entry.

    Workflow:
      4.3a  Verify direccion_entrega_id belongs to the user (ownership check).
      4.3b  Verify forma_pago_id exists and is active.
      4.3c–e FOR each item: lock product row (SELECT FOR UPDATE), validate
             disponible + eliminado_en, validate stock >= cantidad.
      4.3f  Build DetallePedido with precio_snapshot and nombre_snapshot.
      4.3g  Decrement stock_cantidad for each product.
      4.3h  Serialize direccion as JSON string for direccion_snapshot.
      4.3i  Calculate total.
      4.3j  Build Pedido (estado_pedido_id=1 PENDIENTE).
      4.3k  Persist Pedido + detalles via PedidoRepository.create_with_details().
      4.3l  Append HistorialEstadoPedido entry (estado_anterior=None).

    Args:
        request: Validated PedidoCreate payload.
        usuario_id: Authenticated user's primary key.
        uow: Injected UnitOfWork (transaction managed by caller).

    Returns:
        Created Pedido with assigned primary key.

    Raises:
        HTTPException 403: direccion_entrega_id belongs to another user.
        HTTPException 422: forma_pago invalid/inactive, or product invalid
                           (soft-deleted or disponible=False).
        HTTPException 409: Insufficient stock for one or more items (RFC 7807).
    """
    # ------------------------------------------------------------------
    # 4.3a — Ownership check: address belongs to this user
    # ------------------------------------------------------------------
    # Fetch the address via the base repository to check ownership
    direccion = await uow.direcciones_entrega.get_by_id(request.direccion_entrega_id)
    if direccion is None or direccion.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Dirección no autorizada",
                "status": 403,
                "detail": (
                    "La dirección de entrega no existe o no pertenece al usuario autenticado."
                ),
                "instance": "/api/v1/pedidos",
            },
        )

    # ------------------------------------------------------------------
    # 4.3b — Verify forma_pago is active
    # ------------------------------------------------------------------
    forma_pago = await uow.formas_pago.get_by_id(request.forma_pago_id)
    if forma_pago is None or not forma_pago.activo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Forma de pago inválida",
                "status": 422,
                "detail": "La forma de pago especificada no existe o no está activa.",
                "instance": "/api/v1/pedidos",
            },
        )

    # ------------------------------------------------------------------
    # 4.3c–g — Lock products, validate, build detalles, decrement stock
    # ------------------------------------------------------------------
    detalles: list[DetallePedido] = []
    total = Decimal("0.00")

    for item in request.items:
        # 4.3c — SELECT FOR UPDATE to prevent race conditions (RN-PE04)
        producto = await uow.productos.get_by_id_locked(item.producto_id)

        # 4.3d — Validate product is active (get_by_id_locked filters disponible+eliminado_en)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "about:blank",
                    "title": "Producto inválido",
                    "status": 422,
                    "detail": (
                        f"El producto con id={item.producto_id} no existe, "
                        "no está disponible o fue eliminado."
                    ),
                    "instance": "/api/v1/pedidos",
                },
            )

        # 4.3e — Validate stock >= cantidad
        if producto.stock_cantidad < item.cantidad:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "about:blank",
                    "title": "Stock insuficiente",
                    "status": 409,
                    "detail": (
                        f"Stock insuficiente para producto_id={item.producto_id}. "
                        f"Disponible: {producto.stock_cantidad}, "
                        f"solicitado: {item.cantidad}."
                    ),
                    "instance": "/api/v1/pedidos",
                    "producto_id": item.producto_id,
                    "stock_actual": producto.stock_cantidad,
                    "cantidad_solicitada": item.cantidad,
                },
            )

        # 4.3f — Build DetallePedido with snapshots
        detalle = DetallePedido(
            pedido_id=0,  # will be set by repository.create_with_details
            producto_id=producto.id,
            cantidad=item.cantidad,
            precio_snapshot=producto.precio_base,
            nombre_snapshot=producto.nombre,
            ingredientes_excluidos=item.ingredientes_excluidos,
        )
        detalles.append(detalle)

        # 4.3g — Decrement stock
        producto.stock_cantidad -= item.cantidad
        uow.session.add(producto)

        # Accumulate total
        total += producto.precio_base * item.cantidad

    await uow.session.flush()  # Persist stock decrements before Pedido insert

    # ------------------------------------------------------------------
    # 4.3h — Serialize dirección snapshot as JSON string
    # ------------------------------------------------------------------
    direccion_snapshot = json.dumps(
        {
            "alias": direccion.alias,
            "linea1": direccion.linea1,
            "ciudad": direccion.ciudad,
            "codigo_postal": direccion.codigo_postal,
            "piso": direccion.piso,
            "departamento": direccion.departamento,
        },
        ensure_ascii=False,
    )

    # ------------------------------------------------------------------
    # 4.3i–j — Build Pedido
    # ------------------------------------------------------------------
    pedido = Pedido(
        usuario_id=usuario_id,
        direccion_entrega_id=request.direccion_entrega_id,
        forma_pago_id=request.forma_pago_id,
        estado_pedido_id=1,  # PENDIENTE
        total=total,
        observacion=request.observacion,
        direccion_snapshot=direccion_snapshot,
    )

    # ------------------------------------------------------------------
    # 4.3k — Persist Pedido + detalles atomically
    # ------------------------------------------------------------------
    pedido = await uow.pedidos.create_with_details(pedido, detalles)

    # ------------------------------------------------------------------
    # 4.3l — Audit trail entry (estado_anterior=None for initial creation)
    # ------------------------------------------------------------------
    historial = HistorialEstadoPedido(
        pedido_id=pedido.id,
        estado_anterior_id=None,
        estado_nuevo_id=1,  # PENDIENTE
        observacion="Pedido creado",
        usuario_responsable_id=usuario_id,
    )
    await uow.historial_estado_pedido.append(historial)

    return pedido


# ---------------------------------------------------------------------------
# avanzar_estado — Task 4.4
# ---------------------------------------------------------------------------


async def avanzar_estado(
    pedido_id: int,
    nuevo_estado_id: int,
    usuario_id: Optional[int],
    uow: UnitOfWork,
    is_system: bool = False,
) -> Pedido:
    """
    Advance a Pedido through FSM states following VALID_TRANSITIONS.

    Args:
        pedido_id: Primary key of the order.
        nuevo_estado_id: Target state ID (1-6).
        usuario_id: Authenticated user's primary key (logged in historial).
        uow: Injected UnitOfWork.
        is_system: True when called by a system/webhook (allows SYSTEM_ONLY_TARGETS).

    Returns:
        Updated Pedido.

    Raises:
        HTTPException 404: Pedido not found or soft-deleted.
        HTTPException 409: Transition not valid per FSM matrix.
        HTTPException 403: Attempting to set SYSTEM_ONLY_TARGET without system flag.
    """
    # 4.4a — Fetch pedido
    pedido = await uow.pedidos.get_by_id(pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Pedido no encontrado",
                "status": 404,
                "detail": f"El pedido con id={pedido_id} no existe.",
                "instance": f"/api/v1/pedidos/{pedido_id}",
            },
        )

    estado_actual_id = pedido.estado_pedido_id

    # 4.4b — Validate transition via FSM matrix
    allowed = VALID_TRANSITIONS.get(estado_actual_id, [])
    if nuevo_estado_id not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Transición de estado inválida",
                "status": 409,
                "detail": (
                    f"No se puede pasar de "
                    f"{_ESTADO_NOMBRES.get(estado_actual_id, estado_actual_id)} "
                    f"a {_ESTADO_NOMBRES.get(nuevo_estado_id, nuevo_estado_id)}."
                ),
                "instance": f"/api/v1/pedidos/{pedido_id}/estado",
                "estado_actual": estado_actual_id,
                "estado_solicitado": nuevo_estado_id,
            },
        )

    # 4.4c — Check system-only targets (RN-FS02)
    if nuevo_estado_id in SYSTEM_ONLY_TARGETS and not is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Estado reservado para Sistema",
                "status": 403,
                "detail": (
                    f"El estado {_ESTADO_NOMBRES.get(nuevo_estado_id, nuevo_estado_id)} "
                    "solo puede ser asignado por el sistema (webhook de pagos)."
                ),
                "instance": f"/api/v1/pedidos/{pedido_id}/estado",
            },
        )

    # 4.4d — Update state
    pedido_actualizado = await uow.pedidos.update_estado(pedido_id, nuevo_estado_id)

    # 4.4e — Append audit trail
    historial = HistorialEstadoPedido(
        pedido_id=pedido_id,
        estado_anterior_id=estado_actual_id,
        estado_nuevo_id=nuevo_estado_id,
        usuario_responsable_id=usuario_id,
    )
    await uow.historial_estado_pedido.append(historial)

    return pedido_actualizado


# ---------------------------------------------------------------------------
# cancelar — Task 4.5
# ---------------------------------------------------------------------------


async def cancelar(
    pedido_id: int,
    usuario_id: int,
    uow: UnitOfWork,
) -> Pedido:
    """
    Cancel an order and revert all product stock.

    Args:
        pedido_id: Primary key of the order.
        usuario_id: Authenticated user's primary key.
        uow: Injected UnitOfWork.

    Returns:
        Updated Pedido (estado=CANCELADO).

    Raises:
        HTTPException 404: Pedido not found.
        HTTPException 409: Order is already in a terminal state (5 or 6).
    """
    # 4.5a — Fetch pedido
    pedido = await uow.pedidos.get_by_id(pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Pedido no encontrado",
                "status": 404,
                "detail": f"El pedido con id={pedido_id} no existe.",
                "instance": f"/api/v1/pedidos/{pedido_id}/cancelar",
            },
        )

    estado_actual_id = pedido.estado_pedido_id

    # 4.5b — Verify CANCELADO is a valid transition from current state
    allowed = VALID_TRANSITIONS.get(estado_actual_id, [])
    if 6 not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "No se puede cancelar",
                "status": 409,
                "detail": (
                    f"El pedido está en estado "
                    f"{_ESTADO_NOMBRES.get(estado_actual_id, estado_actual_id)} "
                    "y no puede ser cancelado."
                ),
                "instance": f"/api/v1/pedidos/{pedido_id}/cancelar",
                "estado_actual": estado_actual_id,
                "estado_solicitado": 6,
            },
        )

    # 4.5c — Update state to CANCELADO
    pedido_cancelado = await uow.pedidos.update_estado(pedido_id, 6)

    # 4.5d — Revert stock for each DetallePedido
    stmt_result = await uow.pedidos.get_by_id_with_details(pedido_id)
    if stmt_result is not None:
        _, detalles = stmt_result
        for detalle in detalles:
            # Fetch product (no lock needed — we're reverting, not competing)
            producto = await uow.productos.get_by_id(detalle.producto_id)
            if producto is not None:
                producto.stock_cantidad += detalle.cantidad
                uow.session.add(producto)
        await uow.session.flush()

    # 4.5e — Append audit trail
    historial = HistorialEstadoPedido(
        pedido_id=pedido_id,
        estado_anterior_id=estado_actual_id,
        estado_nuevo_id=6,
        observacion="Pedido cancelado",
        usuario_responsable_id=usuario_id,
    )
    await uow.historial_estado_pedido.append(historial)

    return pedido_cancelado


# ---------------------------------------------------------------------------
# confirmar_pedido_por_pago — called by pagos/service.py webhook handler
# ---------------------------------------------------------------------------


async def confirmar_pedido_por_pago(
    pedido_id: int,
    uow: UnitOfWork,
) -> None:
    """
    Transition a Pedido from PENDIENTE(1) → CONFIRMADO(2) triggered by a payment webhook.

    This is a SYSTEM-ONLY transition (is_system=True internally) — cannot be triggered
    manually by users. Called from pagos/service.py after MP payment approval.

    The function delegates to avanzar_estado() with is_system=True so the
    SYSTEM_ONLY_TARGETS guard is satisfied.

    Args:
        pedido_id: Primary key of the order to confirm.
        uow: Injected UnitOfWork (transaction managed by caller, no commit here).

    Raises:
        HTTPException 404: Pedido not found or soft-deleted.
        HTTPException 409: Pedido is not in PENDIENTE state (already confirmed or cancelled).
    """
    # Fetch pedido — 404 if not found
    pedido = await uow.pedidos.get_by_id(pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Pedido no encontrado",
                "status": 404,
                "detail": f"El pedido con id={pedido_id} no existe o fue eliminado.",
                "instance": f"/api/v1/pagos/webhook",
            },
        )

    # Verify pedido is in PENDIENTE state (id=1)
    if pedido.estado_pedido_id != 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Pedido no está en estado PENDIENTE",
                "status": 409,
                "detail": (
                    f"El pedido id={pedido_id} está en estado "
                    f"{_ESTADO_NOMBRES.get(pedido.estado_pedido_id, pedido.estado_pedido_id)} "
                    "y no puede ser confirmado por pago."
                ),
                "instance": f"/api/v1/pagos/webhook",
                "estado_actual": pedido.estado_pedido_id,
            },
        )

    # Delegate to avanzar_estado with is_system=True (bypasses SYSTEM_ONLY_TARGETS guard)
    await avanzar_estado(
        pedido_id=pedido_id,
        nuevo_estado_id=2,  # CONFIRMADO
        usuario_id=None,  # system action — no human user
        uow=uow,
        is_system=True,
    )
