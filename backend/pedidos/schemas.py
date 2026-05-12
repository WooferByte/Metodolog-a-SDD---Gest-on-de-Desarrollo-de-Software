"""
Pydantic v2 request/response schemas for order endpoints.

Validates cantidad >= 1 per line item, items list non-empty.
Sanitizes observacion against XSS.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.sanitize import sanitize_text


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class DetallePedidoCreate(BaseModel):
    """Schema for a single line item in an order creation request."""

    producto_id: int
    cantidad: int = Field(ge=1)
    ingredientes_excluidos: Optional[list[int]] = None


class PedidoCreate(BaseModel):
    """Schema for creating a new order."""

    direccion_entrega_id: int
    forma_pago_id: int
    observacion: Optional[str] = Field(default=None, max_length=500)
    items: list[DetallePedidoCreate] = Field(min_length=1)

    @field_validator("observacion", mode="before")
    @classmethod
    def sanitize_observacion(cls, v: object) -> object:
        """Strip HTML tags from the free-text observation field."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class DetallePedidoResponse(BaseModel):
    """Order line item representation (with price and name snapshots)."""

    id: int
    pedido_id: int
    producto_id: int
    cantidad: int
    precio_snapshot: Decimal
    nombre_snapshot: str
    ingredientes_excluidos: Optional[list[int]]  # Native INTEGER[] (RN-PE07)
    creado_en: datetime

    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    """Order representation."""

    id: int
    usuario_id: int
    direccion_entrega_id: int
    forma_pago_id: int
    estado_pedido_id: int
    total: Decimal
    observacion: Optional[str]
    direccion_snapshot: Optional[str]  # JSON as stored string
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
