"""
Pydantic schemas for role assignment endpoints.

Schemas:
  AssignRoleRequest  — body for PUT /api/v1/admin/users/{user_id}/role
  AssignRoleResponse — response confirming the operation
"""
from typing import Literal

from pydantic import BaseModel, field_validator


# The four fixed roles in the system
VALID_ROLES = {"ADMIN", "STOCK", "PEDIDOS", "CLIENT"}


class AssignRoleRequest(BaseModel):
    """Request body to assign a role to a user."""

    rol_nombre: str

    @field_validator("rol_nombre")
    @classmethod
    def validate_rol_nombre(cls, v: str) -> str:
        """Validate that the role name is one of the four fixed roles."""
        upper = v.upper()
        if upper not in VALID_ROLES:
            raise ValueError(
                f"Invalid role '{v}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
            )
        return upper


class AssignRoleResponse(BaseModel):
    """Response confirming role assignment."""

    user_id: int
    rol_nombre: str
    mensaje: str

    model_config = {"from_attributes": True}
