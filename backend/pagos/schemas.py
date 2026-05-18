"""
Pydantic v2 request/response schemas for payment endpoints.

Supports:
  - CrearPreferenciaRequest: client initiates MP payment preference for an order
  - CrearPreferenciaResponse: returns init_point URL + preference_id + pago_id
  - PagoStatusResponse: current payment state for a pedido
  - WebhookMPPayload: tolerant schema for MP IPN / Webhooks v2
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class CrearPreferenciaRequest(BaseModel):
    """Request to create a MercadoPago payment preference for an order."""

    pedido_id: int


class CrearPreferenciaResponse(BaseModel):
    """Response after creating an MP preference — contains the redirect URL."""

    init_point: str
    preference_id: str
    pago_id: int

    model_config = ConfigDict(from_attributes=True)


class PagoStatusResponse(BaseModel):
    """Current status of the payment for a given order."""

    pago_id: int
    pedido_id: int
    mercadopago_id: Optional[str] = None
    preference_id: Optional[str] = None
    estado: str
    monto: Decimal
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookMPPayload(BaseModel):
    """
    Tolerant schema for MercadoPago IPN / Webhooks v2 notifications.

    MP sends varying payloads depending on the notification type.
    Using extra='allow' to accept any additional fields MP may add.
    """

    topic: Optional[str] = None
    id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    action: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class WebhookStatusResponse(BaseModel):
    """Simple 200 OK response for webhook endpoint."""

    status: str = "ok"
