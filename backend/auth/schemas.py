"""
Pydantic v2 request/response schemas for authentication endpoints.

All free-text fields are sanitized against XSS via field_validator.
Email fields use EmailStr for RFC 5322 format validation.
"""
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.sanitize import sanitize_text


class LoginRequest(BaseModel):
    """Schema for POST /api/v1/auth/login."""

    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    """Schema for POST /api/v1/auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=100)
    apellido: Optional[str] = Field(default=None, max_length=100)

    @field_validator("nombre", "apellido", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v: object) -> object:
        """Strip HTML tags from free-text name fields."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v


class TokenResponse(BaseModel):
    """Schema for successful authentication response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: Optional[Any] = None

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class RefreshRequest(BaseModel):
    """Schema for POST /api/v1/auth/refresh."""

    refresh_token: str = Field(min_length=1)
