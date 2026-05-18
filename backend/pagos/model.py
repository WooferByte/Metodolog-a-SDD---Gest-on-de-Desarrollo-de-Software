"""
SQLModel model for MercadoPago webhook audit log.

PagoWebhookLog: append-only audit trail for every webhook received from MP.
Pago model is defined in core/models.py — not re-defined here.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


class PagoWebhookLog(SQLModel, table=True):
    """
    Append-only audit log for MercadoPago webhooks.

    Records every incoming webhook before processing so we have a full
    audit trail regardless of processing outcome.

    Fields:
    - mercadopago_id: MP payment/notification ID (nullable — topic-dependent)
    - topic: webhook topic (e.g., "payment", "merchant_order")
    - payload: full raw payload as JSONB
    - procesado: True once processing completes without error
    - error_msg: captures exception message if processing fails
    - creado_en: timestamp of reception (append-only, never updated)
    """

    __tablename__ = "pago_webhook_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    mercadopago_id: Optional[str] = Field(default=None, max_length=255, index=True)
    topic: str = Field(max_length=100)
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))
    procesado: bool = Field(default=False)
    error_msg: Optional[str] = Field(default=None)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
