"""
Pydantic v2 schemas for perfil (user profile) endpoints.

Exposes ONLY nombre and telefono — never activo, email, or hashed_password.
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from core.sanitize import sanitize_text


class PerfilUpdate(BaseModel):
    """Schema for partial update of the authenticated user's profile.

    At least one of nombre or telefono must be provided.
    HTML tags are stripped from nombre.
    """

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=20)

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitize_nombre(cls, v: object) -> object:
        """Strip HTML tags from nombre."""
        if isinstance(v, str):
            return sanitize_text(v)
        return v

    @model_validator(mode="after")
    def at_least_one_field(self) -> "PerfilUpdate":
        """Require at least one field to be non-null."""
        if self.nombre is None and self.telefono is None:
            raise ValueError("Provide at least nombre or telefono")
        return self


class CambiarPasswordRequest(BaseModel):
    """Schema for changing the authenticated user's password.

    - Both passwords must have length 8-128.
    - nueva_password must differ from password_actual (validated at schema level → 422).
    """

    password_actual: str = Field(min_length=8, max_length=128)
    nueva_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_must_differ(self) -> "CambiarPasswordRequest":
        """Reject request when nueva_password equals password_actual."""
        if self.password_actual == self.nueva_password:
            raise ValueError("nueva_password must differ from password_actual")
        return self
