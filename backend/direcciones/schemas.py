"""
Pydantic v2 request/response schemas for delivery address endpoints.

Validates field lengths for address components.
Sanitizes alias, linea1, and referencia against XSS.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.sanitize import sanitize_text


class DireccionCreate(BaseModel):
    """Schema for creating a new delivery address."""

    alias: str = Field(min_length=1, max_length=100)
    linea1: str = Field(min_length=1, max_length=255)
    piso: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: str = Field(min_length=1, max_length=100)
    codigo_postal: str = Field(min_length=4, max_length=10)
    referencia: Optional[str] = Field(default=None, max_length=255)
    es_principal: bool = False

    @field_validator("alias", "linea1", "referencia", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text address fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class DireccionUpdate(BaseModel):
    """Schema for partial update of a delivery address."""

    alias: Optional[str] = Field(default=None, min_length=1, max_length=100)
    linea1: Optional[str] = Field(default=None, min_length=1, max_length=255)
    piso: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: Optional[str] = Field(default=None, min_length=1, max_length=100)
    codigo_postal: Optional[str] = Field(default=None, min_length=4, max_length=10)
    referencia: Optional[str] = Field(default=None, max_length=255)
    es_principal: Optional[bool] = None

    @field_validator("alias", "linea1", "referencia", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text address fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class DireccionResponse(BaseModel):
    """Public delivery address representation."""

    id: int
    usuario_id: int
    alias: str
    linea1: str
    piso: Optional[str]
    departamento: Optional[str]
    ciudad: str
    codigo_postal: str
    referencia: Optional[str]
    es_principal: bool
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
