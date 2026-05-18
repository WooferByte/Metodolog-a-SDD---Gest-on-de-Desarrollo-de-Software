"""
PagosService — business logic for MercadoPago payment operations.

Operations:
  - crear_preferencia(): Create an MP payment preference for a PENDIENTE order.
    Returns init_point URL for client redirect.

  - procesar_webhook(): Handle MP IPN/webhook notifications. Validates signature,
    logs to audit trail, updates Pago state, and triggers FSM transition on approval.

  - get_pago_status(): Return current payment status for a given order.

Architecture:
  Router → Service → UoW → Repository → Model
  - Service raises HTTPException — never router, never repository.
  - Service NEVER calls session.commit() directly — UoW manages the lifecycle.
  - Webhook always returns 200 (except invalid signature) to prevent MP retries.

Race condition handling:
  - IntegrityError on mp_payment_id UNIQUE → idempotent, return existing pago.

Webhook signature validation (MP v2):
  - Header format: x-signature: ts=<timestamp>,v1=<hmac_sha256>
  - Manifest: id:<data_id>;request-id:<x-request-id>;ts:<ts>;
  - HMAC-SHA256 with MP_ACCESS_TOKEN as key.
  - In ENV=development: skip signature check (warn only).
"""
import hashlib
import hmac
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.models import Pago
from infrastructure.uow import UnitOfWork
from pagos.model import PagoWebhookLog
from pagos.schemas import (
    CrearPreferenciaResponse,
    PagoStatusResponse,
    WebhookMPPayload,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# crear_preferencia — Task 9.1
# ---------------------------------------------------------------------------


async def crear_preferencia(
    pedido_id: int,
    usuario_id: int,
    sdk,  # mercadopago.SDK instance (injected, avoid circular import)
    uow: UnitOfWork,
) -> CrearPreferenciaResponse:
    """
    Create a MercadoPago payment preference for a PENDIENTE order.

    Workflow:
      1. Fetch pedido — 404 if not found.
      2. Ownership check — 403 if pedido belongs to another user.
      3. State check — 409 if pedido is not PENDIENTE (estado_id=1).
      4. Call MP SDK to create preference.
      5. Create Pago record (preference_id, estado="pending", monto=pedido.total).
      6. Return CrearPreferenciaResponse with init_point URL.

    Args:
        pedido_id: Order to pay for.
        usuario_id: Authenticated user's primary key.
        sdk: MercadoPago SDK instance.
        uow: Injected UnitOfWork (transaction managed by caller).

    Returns:
        CrearPreferenciaResponse with init_point, preference_id, pago_id.

    Raises:
        HTTPException 404: Pedido not found or soft-deleted.
        HTTPException 403: Pedido belongs to another user.
        HTTPException 409: Pedido is not in PENDIENTE state.
        HTTPException 502: MercadoPago SDK error.
    """
    # 9.1a — Fetch pedido
    pedido = await uow.pedidos.get_by_id(pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Pedido no encontrado",
                "status": 404,
                "detail": f"El pedido con id={pedido_id} no existe.",
                "instance": f"/api/v1/pagos/crear-preferencia",
            },
        )

    # 9.1b — Ownership check
    if pedido.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Acceso denegado",
                "status": 403,
                "detail": "El pedido no pertenece al usuario autenticado.",
                "instance": f"/api/v1/pagos/crear-preferencia",
            },
        )

    # 9.1c — State check: pedido must be PENDIENTE (estado_id=1)
    if pedido.estado_pedido_id != 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Pedido no está en estado PENDIENTE",
                "status": 409,
                "detail": (
                    f"No se puede crear una preferencia de pago para un pedido "
                    f"que no está en estado PENDIENTE (estado_id={pedido.estado_pedido_id})."
                ),
                "instance": f"/api/v1/pagos/crear-preferencia",
                "estado_actual": pedido.estado_pedido_id,
            },
        )

    # 9.1d — Build MP preference payload
    external_reference = str(pedido_id)
    preference_data = {
        "items": [
            {
                "id": str(pedido_id),
                "title": f"Pedido #{pedido_id} — Food Store",
                "quantity": 1,
                "unit_price": float(pedido.total),
                "currency_id": "ARS",
            }
        ],
        "external_reference": external_reference,
        "back_urls": {
            "success": "http://localhost:5173/checkout/success",
            "failure": "http://localhost:5173/checkout/failure",
            "pending": "http://localhost:5173/checkout/pending",
        },
        "notification_url": "http://localhost:8000/api/v1/webhooks/mercadopago",
    }

    # 9.1e — Call MP SDK
    try:
        preference_response = sdk.preference().create(preference_data)
        response_body = preference_response.get("response", {})
        if not response_body.get("id"):
            raise ValueError(f"MP SDK returned unexpected response: {preference_response}")
        preference_id = response_body["id"]
        init_point = response_body.get("init_point", "")
    except Exception as exc:
        logger.error("MercadoPago SDK error creating preference: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "type": "about:blank",
                "title": "Error al crear preferencia de pago",
                "status": 502,
                "detail": "No se pudo crear la preferencia de pago con MercadoPago.",
                "instance": "/api/v1/pagos/crear-preferencia",
            },
        )

    # 9.1f — Create Pago record (preference_id field added by migration 010)
    idempotency_key = str(uuid.uuid4())
    pago = Pago(
        pedido_id=pedido_id,
        mp_payment_id=None,  # not yet paid
        mp_status="pending",
        preference_id=preference_id,
        external_reference=external_reference,
        idempotency_key=idempotency_key,
        gateway_response=None,
    )

    pago = await uow.pagos.create(pago)

    return CrearPreferenciaResponse(
        init_point=init_point,
        preference_id=preference_id,
        pago_id=pago.id,
    )


# ---------------------------------------------------------------------------
# _validate_mp_signature — internal helper
# ---------------------------------------------------------------------------


def _validate_mp_signature(
    signature: Optional[str],
    request_id: Optional[str],
    data_id: Optional[str],
) -> bool:
    """
    Validate MercadoPago webhook x-signature header.

    Format: ts=<timestamp>,v1=<hmac_sha256>
    Manifest: id:<data_id>;request-id:<request_id>;ts:<ts>;
    Key: MP_ACCESS_TOKEN

    Args:
        signature: Value of x-signature header.
        request_id: Value of x-request-id header.
        data_id: ID from the webhook payload (data.id or id).

    Returns:
        True if signature is valid, False otherwise.
    """
    if not signature:
        return False

    try:
        parts = {}
        for part in signature.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                parts[k.strip()] = v.strip()

        ts = parts.get("ts")
        v1 = parts.get("v1")

        if not ts or not v1:
            return False

        # Build manifest: id:<data_id>;request-id:<x-request-id>;ts:<ts>;
        manifest_parts = []
        if data_id:
            manifest_parts.append(f"id:{data_id}")
        if request_id:
            manifest_parts.append(f"request-id:{request_id}")
        manifest_parts.append(f"ts:{ts}")
        manifest = ";".join(manifest_parts) + ";"

        # HMAC-SHA256 with MP_ACCESS_TOKEN
        key = settings.mp_access_token.encode("utf-8")
        computed = hmac.new(key, manifest.encode("utf-8"), hashlib.sha256).hexdigest()

        return hmac.compare_digest(computed, v1)
    except Exception as exc:
        logger.warning("Signature validation error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# procesar_webhook — Task 9.2
# ---------------------------------------------------------------------------


async def procesar_webhook(
    payload_raw: dict,
    signature: Optional[str],
    request_id: Optional[str],
    sdk,
    uow: UnitOfWork,
) -> None:
    """
    Handle MercadoPago IPN/webhook notification.

    Workflow:
      1. Extract data_id from payload (data.id or id).
      2. INSERT into pago_webhook_log immediately (before processing).
      3. Validate x-signature (in production — skip in development with warning).
      4. Query MP SDK for actual payment status.
      5. If approved: find/create Pago, update state, call confirmar_pedido_por_pago.
      6. If rejected/cancelled: update Pago.estado only.
      7. Mark log entry as procesado=True.
      8. On exception: log error_msg, return without re-raising (to send 200 to MP).

    Args:
        payload_raw: Raw webhook payload dict.
        signature: x-signature header value.
        request_id: x-request-id header value.
        sdk: MercadoPago SDK instance.
        uow: Injected UnitOfWork (transaction managed by caller).

    Returns:
        None (always — exceptions are caught to prevent MP retries).

    Raises:
        HTTPException 400: Only if signature validation fails in production.
    """
    # 9.2a — Extract relevant IDs from payload
    topic = payload_raw.get("topic") or payload_raw.get("type") or "unknown"
    data_id = None

    if isinstance(payload_raw.get("data"), dict):
        data_id = str(payload_raw["data"].get("id", ""))
    elif payload_raw.get("id"):
        data_id = str(payload_raw.get("id", ""))

    mp_id = data_id or None

    # 9.2b — INSERT into pago_webhook_log BEFORE processing
    log_entry = PagoWebhookLog(
        mercadopago_id=mp_id,
        topic=topic,
        payload=payload_raw,
        procesado=False,
        error_msg=None,
    )
    log_entry = await uow.pago_webhook_logs.create(log_entry)
    await uow.session.flush()

    # 9.2c — Validate signature
    is_production = settings.env == "production"
    if is_production:
        if not _validate_mp_signature(signature, request_id, data_id):
            # Update log entry to mark as failed signature
            log_entry.error_msg = "Invalid x-signature"
            uow.session.add(log_entry)
            await uow.session.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "about:blank",
                    "title": "Firma inválida",
                    "status": 400,
                    "detail": "El header x-signature no es válido.",
                    "instance": "/api/v1/webhooks/mercadopago",
                },
            )
    else:
        if signature:
            is_valid = _validate_mp_signature(signature, request_id, data_id)
            if not is_valid:
                logger.warning(
                    "Webhook signature invalid (ENV=development, continuing anyway). " "mp_id=%s",
                    mp_id,
                )
        else:
            logger.debug("Webhook received without x-signature (ENV=development). mp_id=%s", mp_id)

    # 9.2d — Process payment notification (wrap in try-except to always return 200)
    try:
        if topic not in ("payment", "merchant_order") and not mp_id:
            logger.info("Webhook topic=%s with no mp_id — skipping processing", topic)
            log_entry.procesado = True
            uow.session.add(log_entry)
            await uow.session.flush()
            return

        if not mp_id:
            logger.info("Webhook mp_id is empty — skipping processing")
            log_entry.procesado = True
            uow.session.add(log_entry)
            await uow.session.flush()
            return

        # 9.2e — Query MP for actual payment status
        try:
            payment_response = sdk.payment().get(mp_id)
            http_status = payment_response.get("status")
            if http_status != 200:
                logger.warning(
                    "MP payment %s returned HTTP %s — skipping processing", mp_id, http_status
                )
                log_entry.procesado = True
                uow.session.add(log_entry)
                await uow.session.flush()
                return
            payment_data = payment_response.get("response", {})
            mp_status = str(payment_data.get("status", "unknown"))
            mp_pedido_id_str = payment_data.get("external_reference")
            amount = payment_data.get("transaction_amount", 0)
        except Exception as sdk_exc:
            logger.error("MP SDK error fetching payment %s: %s", mp_id, sdk_exc)
            raise

        # Find pedido_id from external_reference
        pedido_id = None
        if mp_pedido_id_str:
            try:
                pedido_id = int(mp_pedido_id_str)
            except (ValueError, TypeError):
                logger.warning("external_reference is not an int: %s", mp_pedido_id_str)

        # 9.2f — Find or create Pago (handle race condition via IntegrityError)
        existing_pago = await uow.pagos.get_by_mercadopago_id(mp_id)

        if existing_pago is None:
            # Try to create — idempotent via UNIQUE on mercadopago_id
            try:
                new_pago = Pago(
                    pedido_id=pedido_id or 0,
                    mp_payment_id=mp_id,
                    mp_status=mp_status,
                    external_reference=mp_pedido_id_str or mp_id,
                    idempotency_key=str(uuid.uuid4()),
                    gateway_response=str(payment_data)[:5000] if payment_data else None,
                )
                new_pago = await uow.pagos.create(new_pago)
                await uow.session.flush()
                existing_pago = new_pago
            except IntegrityError:
                await uow.session.rollback()
                # Race condition: another request already created the Pago — fetch it
                existing_pago = await uow.pagos.get_by_mercadopago_id(mp_id)
                logger.info("Idempotent webhook: Pago already exists for mp_id=%s", mp_id)
        else:
            # Update existing pago status if changed
            if existing_pago.mp_status != mp_status:
                existing_pago.mp_status = mp_status
                existing_pago.actualizado_en = datetime.utcnow()
                uow.session.add(existing_pago)
                await uow.session.flush()

        # 9.2g — Trigger FSM transition if payment approved
        if mp_status == "approved" and pedido_id:
            try:
                from pedidos.service import confirmar_pedido_por_pago

                await confirmar_pedido_por_pago(pedido_id=pedido_id, uow=uow)
                logger.info("Pedido id=%s confirmed via payment mp_id=%s", pedido_id, mp_id)
            except HTTPException as fsm_exc:
                # Pedido not in PENDIENTE — likely already confirmed (idempotent)
                if fsm_exc.status_code == 409:
                    logger.info(
                        "FSM 409 for pedido_id=%s (already confirmed?) — ignoring", pedido_id
                    )
                elif fsm_exc.status_code == 404:
                    logger.warning("Pedido id=%s not found during webhook processing", pedido_id)
                else:
                    raise

        # 9.2h — Mark log as processed
        log_entry.procesado = True
        uow.session.add(log_entry)
        await uow.session.flush()

    except HTTPException:
        raise  # Let HTTP errors propagate (e.g., signature 400)
    except Exception as exc:
        logger.error("Error processing webhook mp_id=%s: %s", mp_id, exc, exc_info=True)
        try:
            log_entry.error_msg = str(exc)[:1000]
            uow.session.add(log_entry)
            await uow.session.flush()
        except Exception:
            pass  # Don't fail if log update fails
        # Return without re-raising — prevents MP from retrying
        return


# ---------------------------------------------------------------------------
# get_pago_status — Task 9.3
# ---------------------------------------------------------------------------


async def get_pago_status(
    pedido_id: int,
    usuario_id: int,
    es_admin: bool,
    uow: UnitOfWork,
) -> PagoStatusResponse:
    """
    Return current payment status for a given order.

    Args:
        pedido_id: Order primary key.
        usuario_id: Authenticated user's primary key.
        es_admin: True if user has ADMIN role.
        uow: Injected UnitOfWork.

    Returns:
        PagoStatusResponse with current payment data.

    Raises:
        HTTPException 404: Pedido or Pago not found.
        HTTPException 403: Non-admin requesting another user's payment status.
    """
    # 9.3a — Fetch pedido
    pedido = await uow.pedidos.get_by_id(pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Pedido no encontrado",
                "status": 404,
                "detail": f"El pedido con id={pedido_id} no existe.",
                "instance": f"/api/v1/pagos/{pedido_id}/status",
            },
        )

    # 9.3b — Ownership check (non-admin)
    if not es_admin and pedido.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Acceso denegado",
                "status": 403,
                "detail": "No tiene permiso para consultar el estado de pago de este pedido.",
                "instance": f"/api/v1/pagos/{pedido_id}/status",
            },
        )

    # 9.3c — Fetch Pago
    pago = await uow.pagos.get_by_pedido_id(pedido_id)
    if pago is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Pago no encontrado",
                "status": 404,
                "detail": f"No se encontró un pago para el pedido id={pedido_id}.",
                "instance": f"/api/v1/pagos/{pedido_id}/status",
            },
        )

    return PagoStatusResponse(
        pago_id=pago.id,
        pedido_id=pago.pedido_id,
        mercadopago_id=pago.mp_payment_id,
        preference_id=getattr(pago, "preference_id", None),
        estado=pago.mp_status or "pending",
        monto=pedido.total,
        creado_en=pago.creado_en,
        actualizado_en=pago.actualizado_en,
    )
