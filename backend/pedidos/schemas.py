"""
Pydantic v2 request/response schemas for order endpoints.

Validates cantidad >= 1 per line item, items list non-empty.
Sanitizes observacion against XSS.

Also contains validation schemas for pre-checkout cart validation:
  - ValidarItemRequest
  - ValidarCarritoRequest
  - StockInsuficienteItem
  - CambioPrecioItem
  - ValidarCarritoResponse
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.sanitize import sanitize_text


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cart validation schemas (checkout-pre-validation)
# ---------------------------------------------------------------------------


class ValidarItemRequest(BaseModel):
    """A single cart item sent for pre-checkout validation.

    Fields:
        producto_id: The product's primary key in the database.
        cantidad: Quantity requested by the user (must be >= 1).
        precio_carrito: Price stored in the client cart at the time of addItem().
            Used for price-drift detection against the current DB price.
    """

    producto_id: int
    cantidad: int = Field(ge=1)
    precio_carrito: Decimal


class ValidarCarritoRequest(BaseModel):
    """Request body for POST /api/v1/pedidos/validar.

    Fields:
        items: Non-empty list of cart items to validate.
        direccion_id: ID of the selected delivery address.
    """

    items: list[ValidarItemRequest] = Field(min_length=1)
    direccion_id: int


class StockInsuficienteItem(BaseModel):
    """Describes a single stock-shortage issue.

    Returned when a cart item requests more units than available.
    """

    producto_id: int
    nombre: str
    stock_actual: int
    cantidad_solicitada: int


class CambioPrecioItem(BaseModel):
    """Describes a single price-drift issue.

    Returned when the cart-stored price differs from the current DB price
    by more than 0.01 (1-cent tolerance).
    """

    producto_id: int
    precio_carrito: Decimal
    precio_actual: Decimal


class ValidarCarritoResponse(BaseModel):
    """Structured validation report returned by POST /api/v1/pedidos/validar.

    HTTP 200 — soft warnings (stock issues, price changes, or clean).
    HTTP 422 — hard blocks (empty cart or missing address — never reaches this
               schema; they are raised as HTTPException before this is returned).

    Fields:
        stock_insuficiente: Products where requested qty > available stock.
        productos_invalidos: Product IDs that are unavailable (soft-deleted,
            disponible=False, or not found in DB).
        cambios_de_precio: Products where cart price drifted from DB price.
        carrito_vacio: True if the submitted items list was empty (hard block).
        sin_direccion: True if the user has no active delivery addresses (hard block).
    """

    stock_insuficiente: list[StockInsuficienteItem] = Field(default_factory=list)
    productos_invalidos: list[int] = Field(default_factory=list)
    cambios_de_precio: list[CambioPrecioItem] = Field(default_factory=list)
    carrito_vacio: bool = False
    sin_direccion: bool = False


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


class PedidoDetailResponse(PedidoResponse):
    """Order representation with line items and FSM audit trail."""

    detalles: list[DetallePedidoResponse]
    historial: list["HistorialEstadoResponse"] = []


class AvanzarEstadoRequest(BaseModel):
    """Request body for advancing a Pedido state via FSM transition."""

    nuevo_estado_id: int = Field(ge=1, le=6)
    observacion: Optional[str] = Field(default=None, max_length=500)

    @field_validator("observacion", mode="before")
    @classmethod
    def sanitize_observacion(cls, v: object) -> object:
        """Strip HTML tags from the free-text observation field."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class PaginatedPedidosResponse(BaseModel):
    """Paginated list of orders for a user.

    Fields:
        items: Page of Pedido objects (non-deleted, newest first).
        total: Total count of non-deleted orders for the user (for UI pagination).
        limit: Page size applied in this request.
        offset: Offset applied in this request.
    """

    items: list[PedidoResponse]
    total: int
    limit: int
    offset: int


class HistorialEstadoResponse(BaseModel):
    """Audit trail entry for an order status change."""

    id: int
    pedido_id: int
    estado_anterior_id: Optional[int]
    estado_nuevo_id: int
    observacion: Optional[str]
    usuario_responsable_id: Optional[int]
    usuario_email: Optional[str] = None
    creado_en: datetime

    model_config = {"from_attributes": True}
