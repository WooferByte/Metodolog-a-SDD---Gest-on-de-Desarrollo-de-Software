"""
PedidosService — business logic for order-related operations.

Current operations:
  - validar_carrito(): Pre-checkout validation. Read-only advisory check that
    detects empty cart, missing address, insufficient stock, and price drift.
    Returns a structured ValidarCarritoResponse without mutating any DB state.

Architecture:
  Router → Service → UoW → Repository → Model
  - Service raises HTTPException (422) for hard blocks (empty cart / no address).
  - Service returns ValidarCarritoResponse (200) for soft warnings (stock/price).
  - Service NEVER calls session.commit() directly — UoW manages the lifecycle.
"""
from decimal import Decimal

from fastapi import HTTPException, status

from infrastructure.uow import UnitOfWork
from pedidos.schemas import (
    CambioPrecioItem,
    StockInsuficienteItem,
    ValidarCarritoRequest,
    ValidarCarritoResponse,
)


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
