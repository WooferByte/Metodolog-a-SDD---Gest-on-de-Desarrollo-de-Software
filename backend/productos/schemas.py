"""
Pydantic v2 request/response schemas for product endpoints.

Validates precio_base > 0, stock_cantidad >= 0.
Sanitizes nombre and descripcion against XSS.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from core.sanitize import sanitize_text


class ProductoCreate(BaseModel):
    """Schema for creating a new product."""

    nombre: str = Field(min_length=1, max_length=255)
    descripcion: Optional[str] = None
    precio_base: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    stock_cantidad: int = Field(default=0, ge=0)
    disponible: bool = True
    imagen_url: Optional[str] = None

    @field_validator("nombre", "descripcion", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class ProductoUpdate(BaseModel):
    """Schema for partial update of a product (all fields optional)."""

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    precio_base: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=10)
    stock_cantidad: Optional[int] = Field(default=None, ge=0)
    disponible: Optional[bool] = None
    imagen_url: Optional[str] = None

    @field_validator("nombre", "descripcion", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class ProductoStockUpdate(BaseModel):
    """Schema for stock-only patch endpoint."""

    stock_cantidad: int = Field(ge=0)


class CategoriaCompacta(BaseModel):
    """Compact category representation for product responses."""

    id: int
    nombre: str
    padre_id: Optional[int]

    model_config = {"from_attributes": True}


class ProductoCategoriaSetRequest(BaseModel):
    """Request body for PUT /productos/{id}/categorias — full replacement."""

    categoria_ids: List[int] = Field(
        default_factory=list,
        description="List of category IDs to associate. Empty list removes all associations.",
    )

    @field_validator("categoria_ids")
    @classmethod
    def validate_categoria_ids(cls, v: List[int]) -> List[int]:
        """Accept any list including empty (empty = remove all associations)."""
        return v


class IngredienteAsociacion(BaseModel):
    """Single ingredient association entry for PUT /productos/{id}/ingredientes."""

    ingrediente_id: int
    es_removible: bool = False


class IngredienteCompacto(BaseModel):
    """Compact ingredient representation for product responses.

    es_removible comes from the pivot table (ProductoIngrediente), not from Ingrediente.
    """

    id: int
    nombre: str
    es_alergeno: bool
    es_removible: bool

    model_config = {"from_attributes": True}


class ProductoIngredienteSetRequest(BaseModel):
    """Request body for PUT /productos/{id}/ingredientes — full replacement."""

    ingredientes: List[IngredienteAsociacion] = Field(
        default_factory=list,
        description=(
            "List of ingredient associations. "
            "Empty list removes all associations."
        ),
    )


class ProductoResponse(BaseModel):
    """Public product representation."""

    id: int
    nombre: str
    descripcion: Optional[str]
    precio_base: Decimal
    stock_cantidad: int
    disponible: bool
    imagen_url: Optional[str]
    creado_en: datetime
    categorias: List[CategoriaCompacta] = []
    ingredientes: List[IngredienteCompacto] = []

    model_config = {"from_attributes": True}
