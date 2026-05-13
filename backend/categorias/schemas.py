"""
Pydantic v2 request/response schemas for category endpoints.

Validates nombre is not blank (strips whitespace before length check).
Sanitizes nombre and descripcion against XSS.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.sanitize import sanitize_text


class CategoriaCreate(BaseModel):
    """Schema for creating a new product category."""

    nombre: str = Field(min_length=1, max_length=255)
    descripcion: Optional[str] = None
    padre_id: Optional[int] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitize_and_strip_nombre(cls, v: object) -> object:
        """
        Sanitize XSS then strip whitespace.
        Ensures whitespace-only values fail the min_length=1 check.
        """
        if isinstance(v, str):
            v = sanitize_text(v)
            return v.strip() if v else v
        return v

    @field_validator("descripcion", mode="before")
    @classmethod
    def sanitize_descripcion(cls, v: object) -> object:
        """Strip HTML tags from descripcion."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class CategoriaUpdate(BaseModel):
    """Schema for partial update of a category (all fields optional)."""

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    padre_id: Optional[int] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitize_and_strip_nombre(cls, v: object) -> object:
        if isinstance(v, str):
            v = sanitize_text(v)
            return v.strip() if v else v
        return v

    @field_validator("descripcion", mode="before")
    @classmethod
    def sanitize_descripcion(cls, v: object) -> object:
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class CategoriaResponse(BaseModel):
    """Public category representation."""

    id: int
    nombre: str
    descripcion: Optional[str]
    padre_id: Optional[int]
    creado_en: datetime

    model_config = {"from_attributes": True}


class CategoriaTreeItem(CategoriaResponse):
    """
    Category representation enriched with tree depth.

    Used by GET /categorias/tree and GET /categorias/{id}/subtree.
    The depth field allows frontends to render indentation without
    re-computing the hierarchy client-side.
    """

    depth: int
