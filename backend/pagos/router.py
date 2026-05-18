"""
Pagos Router — HTTP handlers for MercadoPago payment endpoints.

Routes:
  POST /api/v1/pagos/crear-preferencia
    - Creates an MP payment preference for a PENDIENTE order.
    - Requires CLIENT role. Rate-limited: 5/minute per IP.

  GET /api/v1/pagos/{pedido_id}/status
    - Returns current payment status for an order.
    - Requires CLIENT or ADMIN role.

  POST /api/v1/webhooks/mercadopago
    - Receives MP IPN/webhook notifications.
    - Public endpoint — no JWT, no rate limiting.
    - Always returns 200 (except invalid signature in production).

Architecture: Router → Service → UoW → Repository → Model
  - Router handles HTTP only: parse request, validate schema, call service.
  - Never contains business logic.
  - All endpoints have explicit response_model.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse

from core.dependencies import get_current_user, get_mp_sdk, require_role
from core.limiter import limiter
from core.models import Usuario
from infrastructure.uow import UnitOfWork, get_uow
from pagos.schemas import (
    CrearPreferenciaRequest,
    CrearPreferenciaResponse,
    PagoStatusResponse,
    WebhookMPPayload,
    WebhookStatusResponse,
)
from pagos import service as pagos_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pagos router
# ---------------------------------------------------------------------------

pagos_router = APIRouter(prefix="/pagos", tags=["pagos"])
webhooks_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ---------------------------------------------------------------------------
# POST /pagos/crear-preferencia
# ---------------------------------------------------------------------------


@pagos_router.post(
    "/crear-preferencia",
    response_model=CrearPreferenciaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear preferencia de pago MercadoPago",
    description=(
        "Crea una preferencia de pago en MercadoPago para un pedido en estado PENDIENTE. "
        "Retorna el init_point URL para redirigir al usuario a la página de pago de MP."
    ),
)
@limiter.limit("5/minute")
async def crear_preferencia(
    request: Request,  # required by slowapi
    body: CrearPreferenciaRequest,
    current_user: Usuario = Depends(require_role(["CLIENT"])),
    sdk=Depends(get_mp_sdk),
    uow: UnitOfWork = Depends(get_uow),
) -> CrearPreferenciaResponse:
    """Create a MercadoPago payment preference for a PENDIENTE order."""
    async with uow:
        return await pagos_service.crear_preferencia(
            pedido_id=body.pedido_id,
            usuario_id=current_user.id,
            sdk=sdk,
            uow=uow,
        )


# ---------------------------------------------------------------------------
# GET /pagos/{pedido_id}/status
# ---------------------------------------------------------------------------


@pagos_router.get(
    "/{pedido_id}/status",
    response_model=PagoStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado de pago de un pedido",
    description=(
        "Retorna el estado actual del pago asociado al pedido. "
        "CLIENT solo puede consultar sus propios pedidos. ADMIN puede consultar cualquier pedido."
    ),
)
async def get_pago_status(
    pedido_id: int,
    current_user: Usuario = Depends(require_role(["CLIENT", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> PagoStatusResponse:
    """Return current payment status for a given order."""
    es_admin = any(r.nombre == "ADMIN" for r in current_user.roles)
    async with uow:
        return await pagos_service.get_pago_status(
            pedido_id=pedido_id,
            usuario_id=current_user.id,
            es_admin=es_admin,
            uow=uow,
        )


# ---------------------------------------------------------------------------
# POST /webhooks/mercadopago
# ---------------------------------------------------------------------------


@webhooks_router.post(
    "/mercadopago",
    response_model=WebhookStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Webhook MercadoPago IPN",
    description=(
        "Recibe notificaciones IPN de MercadoPago. Endpoint público (sin JWT). "
        "Siempre retorna 200 para evitar reintentos, salvo firma inválida en producción (400)."
    ),
)
async def mercadopago_webhook(
    request: Request,
    payload: WebhookMPPayload,
    x_signature: Optional[str] = Header(None, alias="x-signature"),
    x_request_id: Optional[str] = Header(None, alias="x-request-id"),
    sdk=Depends(get_mp_sdk),
    uow: UnitOfWork = Depends(get_uow),
) -> WebhookStatusResponse:
    """Handle MercadoPago IPN/webhook notification."""
    payload_raw = payload.model_dump(mode="json")

    async with uow:
        await pagos_service.procesar_webhook(
            payload_raw=payload_raw,
            signature=x_signature,
            request_id=x_request_id,
            sdk=sdk,
            uow=uow,
        )

    return WebhookStatusResponse(status="ok")
