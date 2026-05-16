"""
PedidosRouter — HTTP endpoints for order operations.

Endpoints:
  POST /pedidos/validar             — Pre-checkout cart validation (CLIENT, read-only).
  POST /pedidos                     — Create a new order (CLIENT, rate-limited 10/hour/user).
  GET  /pedidos                     — List own orders with pagination (CLIENT).
  GET  /pedidos/{pedido_id}         — Get order detail with ownership check (CLIENT/ADMIN).
  PATCH /pedidos/{pedido_id}/estado — Advance FSM state (ADMIN only).
  DELETE /pedidos/{pedido_id}       — Cancel + soft-delete order (CLIENT/ADMIN).

Authentication & Authorization:
  All endpoints require JWT auth via require_role() from core.dependencies.
  CLIENT can only access/modify their own orders (ownership check → 403).
  ADMIN can access/modify any order.

Architecture:
  Router → Service → UoW → Repository
  - Router is HTTP-only: parses request, delegates to service, returns response.
  - Service raises HTTPException — never the router.
  - No session.commit() here — UoW context manager handles it.

Rate limiting:
  POST /pedidos: 10 requests/hour per usuario_id (US-073).
  Key func uses current_user.id so two users behind the same NAT don't share quota.
"""
from datetime import datetime, timezone

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status

from core.dependencies import require_role
from core.limiter import limiter
from core.models import Usuario
from infrastructure.uow import UnitOfWork, get_uow
from pedidos import service
from pedidos.schemas import (
    AvanzarEstadoRequest,
    PaginatedPedidosResponse,
    PedidoCreate,
    PedidoDetailResponse,
    PedidoResponse,
    ValidarCarritoRequest,
    ValidarCarritoResponse,
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


# ---------------------------------------------------------------------------
# POST /pedidos/validar  — Pre-checkout cart validation (CLIENT only, read-only)
# ---------------------------------------------------------------------------


@router.post(
    "/validar",
    response_model=ValidarCarritoResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar carrito pre-checkout",
    description=(
        "Valida el contenido del carrito antes de proceder al checkout. "
        "Verifica: carrito vacío, dirección inexistente (HTTP 422), "
        "stock insuficiente y cambios de precio (HTTP 200 con warnings). "
        "Endpoint read-only — no muta ningún dato."
    ),
    responses={
        200: {"description": "Validación completa (puede incluir warnings de stock/precio)"},
        401: {"description": "No autenticado"},
        403: {"description": "Rol insuficiente (requiere CLIENT)"},
        422: {"description": "Carrito vacío o sin dirección de entrega (RFC 7807)"},
    },
)
async def validar_carrito(
    request: ValidarCarritoRequest,
    current_user: Usuario = Depends(require_role(["CLIENT"])),
    uow: UnitOfWork = Depends(get_uow),
) -> ValidarCarritoResponse:
    """
    Pre-checkout cart validation endpoint.

    Accepts the current cart items (with cart-stored prices) and a
    selected delivery address ID. Returns a structured validation report.

    Hard blocks (HTTP 422):
      - items list is empty
      - user has no active delivery addresses

    Soft warnings (HTTP 200 with non-empty arrays):
      - stock_insuficiente: qty requested > available stock
      - productos_invalidos: product is soft-deleted, unavailable, or not found
      - cambios_de_precio: cart price drifted from current DB price by > 0.01

    Clean validation (HTTP 200 with all empty arrays):
      - All items are available with sufficient stock and matching prices.
    """
    async with uow:
        result = await service.validar_carrito(request, current_user.id, uow)
    return result


# ---------------------------------------------------------------------------
# POST /pedidos  — Create a new order (CLIENT, rate-limited 10/hour per user)
# ---------------------------------------------------------------------------


def _pedido_rate_key(request: Request) -> str:
    """
    Rate-limit key for POST /pedidos: one bucket per usuario_id.

    Two users behind the same NAT share the same IP but different user_ids.
    This ensures 10 pedidos/hour is enforced per user (US-073), not per IP.

    The current_user.id is injected into request.state by the dependency
    resolution chain: we extract it from state if available, otherwise fall
    back to remote address (should never happen since require_role enforces auth).
    """
    user_id = getattr(request.state, "pedido_user_id", None)
    if user_id is not None:
        return f"create_pedido:{user_id}"
    # Fallback — should not be reached (auth required before rate check)
    from slowapi.util import get_remote_address

    return f"create_pedido:{get_remote_address(request)}"


@router.post(
    "",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo pedido",
    description=(
        "Crea un nuevo pedido para el usuario autenticado. "
        "Decrementa stock, guarda snapshots de precio y dirección, "
        "e inicia el flujo FSM en estado PENDIENTE. "
        "Rate-limitado: 10 pedidos/hora por usuario (US-073)."
    ),
    responses={
        201: {"description": "Pedido creado. Header Location apunta al recurso creado."},
        401: {"description": "No autenticado"},
        403: {"description": "Rol insuficiente (requiere CLIENT) o dirección de otro usuario"},
        409: {"description": "Stock insuficiente para uno o más productos (RFC 7807)"},
        422: {"description": "Forma de pago inválida o producto no disponible (RFC 7807)"},
        429: {"description": "Rate limit excedido — 10 pedidos/hora por usuario"},
    },
)
@limiter.limit("10/hour", key_func=_pedido_rate_key)
async def create_pedido(
    request: Request,
    body: PedidoCreate,
    response: Response,
    current_user: Usuario = Depends(require_role(["CLIENT"])),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoResponse:
    """
    Create a new order for the authenticated CLIENT.

    Performs ownership check on direccion_entrega_id, validates forma_pago,
    locks products (SELECT FOR UPDATE), checks stock, builds snapshots,
    decrements stock, and inserts Pedido + DetallePedido atomically.

    Rate limit: 10 requests/hour per usuario_id (not per IP).
    """
    # Inject user_id into request.state so _pedido_rate_key can read it
    # (resolved before @limiter.limit executes the actual request counting)
    request.state.pedido_user_id = current_user.id

    async with uow:
        pedido = await service.create_pedido(body, current_user.id, uow)

    response.headers["Location"] = f"/api/v1/pedidos/{pedido.id}"
    return PedidoResponse.model_validate(pedido)


# ---------------------------------------------------------------------------
# GET /pedidos  — List own orders with pagination (CLIENT)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PaginatedPedidosResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar pedidos",
    description=(
        "CLIENT: retorna solo sus propios pedidos. "
        "ADMIN/PEDIDOS: retorna todos los pedidos del sistema. "
        "Excluye soft-deleted. Orden: más recientes primero."
    ),
    responses={
        200: {"description": "Lista paginada de pedidos"},
        401: {"description": "No autenticado"},
        403: {"description": "Rol insuficiente (requiere CLIENT, ADMIN o PEDIDOS)"},
    },
)
async def list_pedidos(
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados por página"),
    offset: int = Query(default=0, ge=0, description="Número de resultados a saltar"),
    estado_pedido_id: Optional[int] = Query(default=None, description="Filtrar por estado (1-6)"),
    q: Optional[str] = Query(default=None, description="Buscar por email de usuario (solo ADMIN/PEDIDOS)"),
    fecha_desde: Optional[str] = Query(default=None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(default=None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Usuario = Depends(require_role(["CLIENT", "ADMIN", "PEDIDOS"])),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginatedPedidosResponse:
    """
    CLIENT → own orders only (filters ignored except estado_pedido_id).
    ADMIN/PEDIDOS → all orders with optional filters (q, estado, fecha).
    """
    user_roles = {r.nombre for r in current_user.roles}
    is_staff = bool(user_roles & {"ADMIN", "PEDIDOS"})

    async with uow:
        if is_staff:
            items = await uow.pedidos.list_all(
                skip=offset, limit=limit,
                estado_pedido_id=estado_pedido_id,
                q=q, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
            )
            total = await uow.pedidos.count_all(
                estado_pedido_id=estado_pedido_id,
                q=q, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
            )
        else:
            items = await uow.pedidos.list_by_usuario(current_user.id, skip=offset, limit=limit)
            total = await uow.pedidos.count_by_usuario(current_user.id)

    return PaginatedPedidosResponse(
        items=[PedidoResponse.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# GET /pedidos/{pedido_id}  — Get order detail (CLIENT/ADMIN with ownership)
# ---------------------------------------------------------------------------


@router.get(
    "/{pedido_id}",
    response_model=PedidoDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de un pedido",
    description=(
        "Retorna el detalle completo de un pedido (con líneas de detalle). "
        "CLIENT solo puede ver sus propios pedidos (403 si pertenece a otro usuario). "
        "ADMIN puede ver cualquier pedido."
    ),
    responses={
        200: {"description": "Detalle del pedido con sus líneas"},
        401: {"description": "No autenticado"},
        403: {"description": "El pedido no pertenece al usuario autenticado (RFC 7807)"},
        404: {"description": "Pedido no encontrado o soft-deleted (RFC 7807)"},
    },
)
async def get_pedido(
    pedido_id: int,
    current_user: Usuario = Depends(require_role(["CLIENT", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoDetailResponse:
    """
    Get a single order with full detail.

    Ownership check (D-02): if the authenticated user is CLIENT and the order
    belongs to another user → 403 (never 404, to avoid leaking existence).
    ADMIN skips the ownership check.
    """
    async with uow:
        result = await uow.pedidos.get_by_id_with_details(pedido_id)

    if result is None:
        from fastapi import HTTPException

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

    pedido, detalles = result

    # Ownership check: CLIENT can only see their own orders
    user_roles = {r.nombre for r in current_user.roles}
    if "ADMIN" not in user_roles and pedido.usuario_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Acceso denegado",
                "status": 403,
                "detail": "No tenés permiso para ver este pedido.",
                "instance": f"/api/v1/pedidos/{pedido_id}",
            },
        )

    return PedidoDetailResponse(
        **PedidoResponse.model_validate(pedido).model_dump(),
        detalles=[d if hasattr(d, "__dict__") else d for d in detalles],
    )


# ---------------------------------------------------------------------------
# PATCH /pedidos/{pedido_id}/estado  — Advance FSM state (ADMIN only)
# ---------------------------------------------------------------------------


@router.patch(
    "/{pedido_id}/estado",
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK,
    summary="Avanzar estado del pedido (ADMIN)",
    description=(
        "Avanza el estado del pedido según la FSM de pedidos. "
        "Solo ADMIN puede llamar este endpoint. "
        "CLIENT nunca puede auto-confirmar su pedido (D-05). "
        "Transición inválida → HTTP 409."
    ),
    responses={
        200: {"description": "Estado actualizado correctamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Rol insuficiente (requiere ADMIN)"},
        404: {"description": "Pedido no encontrado (RFC 7807)"},
        409: {"description": "Transición de estado inválida per FSM (RFC 7807)"},
    },
)
async def avanzar_estado(
    pedido_id: int,
    body: AvanzarEstadoRequest,
    current_user: Usuario = Depends(require_role(["ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoResponse:
    """
    Advance a Pedido's FSM state (ADMIN only).

    The service validates the transition matrix. SYSTEM_ONLY_TARGETS
    (e.g. CONFIRMADO=2) require is_system=True; this endpoint passes
    is_system=False, so ADMIN cannot manually set CONFIRMADO either
    (that's reserved for the payment webhook).
    """
    async with uow:
        pedido = await service.avanzar_estado(
            pedido_id,
            body.nuevo_estado_id,
            current_user.id,
            uow,
            is_system=False,
        )

    return PedidoResponse.model_validate(pedido)


# ---------------------------------------------------------------------------
# DELETE /pedidos/{pedido_id}  — Cancel + soft-delete order (CLIENT/ADMIN)
# ---------------------------------------------------------------------------


@router.delete(
    "/{pedido_id}",
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancelar y ocultar un pedido",
    description=(
        "Cancela el pedido (FSM → CANCELADO, stock revertido) y lo marca como "
        "eliminado (soft delete con eliminado_en) en la misma transacción atómica. "
        "CLIENT solo puede cancelar sus propios pedidos en estado PENDIENTE. "
        "ADMIN puede cancelar cualquier pedido cancelable (sin restricción de estado PENDIENTE). "
        "Soft-deleted → ya no aparece en GET /pedidos. "
        "Nunca hace hard delete (D-04)."
    ),
    responses={
        200: {"description": "Pedido cancelado y soft-deleted"},
        401: {"description": "No autenticado"},
        403: {"description": "No pertenece al usuario o rol insuficiente (RFC 7807)"},
        404: {"description": "Pedido no encontrado (RFC 7807)"},
        409: {"description": "Pedido en estado que no permite cancelación (RFC 7807)"},
    },
)
async def delete_pedido(
    pedido_id: int,
    current_user: Usuario = Depends(require_role(["CLIENT", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoResponse:
    """
    Cancel an order and soft-delete it atomically.

    Steps (D-04):
      1. Fetch the order — 404 if not found.
      2. Ownership check for CLIENT — 403 if not the owner.
      3. CLIENT-only state check — 409 if not in PENDIENTE (estado_id=1).
         ADMIN can cancel any cancellable state (service validates FSM).
      4. Call service.cancelar() — FSM → CANCELADO, stock reverted, historial appended.
      5. Set eliminado_en = utcnow() — soft delete within the same UoW transaction.

    All steps run inside a single `async with uow:` block for atomicity.
    """
    from fastapi import HTTPException

    async with uow:
        # Step 1: fetch order
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

        # Step 2: ownership check (CLIENT only — ADMIN bypasses)
        user_roles = {r.nombre for r in current_user.roles}
        if "ADMIN" not in user_roles and pedido.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Acceso denegado",
                    "status": 403,
                    "detail": "No tenés permiso para cancelar este pedido.",
                    "instance": f"/api/v1/pedidos/{pedido_id}",
                },
            )

        # Step 3: CLIENT restriction — only PENDIENTE (estado_id=1) is self-cancellable
        if "ADMIN" not in user_roles and pedido.estado_pedido_id != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "about:blank",
                    "title": "No se puede cancelar",
                    "status": 409,
                    "detail": (
                        "Los clientes solo pueden cancelar pedidos en estado PENDIENTE. "
                        f"El pedido está en estado_id={pedido.estado_pedido_id}."
                    ),
                    "instance": f"/api/v1/pedidos/{pedido_id}",
                    "estado_actual": pedido.estado_pedido_id,
                },
            )

        # Step 4: FSM cancel (validates transition, reverts stock, appends historial)
        pedido_cancelado = await service.cancelar(pedido_id, current_user.id, uow)

        # Step 5: soft delete — set eliminado_en in same transaction
        pedido_cancelado.eliminado_en = datetime.now(timezone.utc).replace(tzinfo=None)
        uow.session.add(pedido_cancelado)

    return PedidoResponse.model_validate(pedido_cancelado)
