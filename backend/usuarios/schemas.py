"""
Pydantic v2 request/response schemas for user management endpoints.

Does NOT expose hashed_password or eliminado_en in responses.
All free-text name fields are sanitized against XSS.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.sanitize import sanitize_text


class UsuarioCreate(BaseModel):
    """Schema for creating a new user (admin use or self-registration)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=100)
    apellido: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=20)

    @field_validator("nombre", "apellido", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text name fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class UsuarioUpdate(BaseModel):
    """Schema for partial update of a user account."""

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=20)
    activo: Optional[bool] = None

    @field_validator("nombre", "apellido", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text name fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class UsuarioResponse(BaseModel):
    """Public-safe user representation — never exposes hashed_password."""

    id: int
    email: str
    nombre: str
    apellido: Optional[str]
    activo: bool
    telefono: Optional[str]
    creado_en: datetime

    model_config = {"from_attributes": True}
