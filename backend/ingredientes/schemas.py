"""
Pydantic v2 request/response schemas for ingredient endpoints.

Sanitizes nombre against XSS.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.sanitize import sanitize_text


class IngredienteCreate(BaseModel):
    """Schema for creating a new ingredient."""

    nombre: str = Field(min_length=1, max_length=255)
    es_alergeno: bool = False

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitize_nombre(cls, v: object) -> object:
        """Strip HTML tags from nombre."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class IngredienteUpdate(BaseModel):
    """Schema for partial update of an ingredient."""

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    es_alergeno: Optional[bool] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitize_nombre(cls, v: object) -> object:
        """Strip HTML tags from nombre."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class IngredienteResponse(BaseModel):
    """Public ingredient representation."""

    id: int
    nombre: str
    es_alergeno: bool
    creado_en: datetime

    model_config = {"from_attributes": True}
