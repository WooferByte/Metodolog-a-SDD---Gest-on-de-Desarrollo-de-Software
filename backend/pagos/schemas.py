"""
Pydantic v2 request/response schemas for payment endpoints.

Supports MercadoPago IPN webhook validation and payment creation.
No free-text fields — no XSS sanitization needed here.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PagoCreate(BaseModel):
    """Schema for initiating a payment for an existing order."""

    pedido_id: int
    forma_pago_id: int


class WebhookIPNRequest(BaseModel):
    """
    Schema for MercadoPago IPN (Instant Payment Notification) webhook.

    MercadoPago sends POST requests with these fields when a payment status changes.
    See: https://www.mercadopago.com/developers/en/guides/notifications/ipn
    """

    id: str
    topic: str


class PagoResponse(BaseModel):
    """Payment representation."""

    id: int
    pedido_id: int
    mp_payment_id: Optional[str]
    mp_status: Optional[str]
    external_reference: str
    creado_en: datetime

    model_config = {"from_attributes": True}
