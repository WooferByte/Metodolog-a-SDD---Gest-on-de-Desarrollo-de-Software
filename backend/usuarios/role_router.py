"""
Role management router — admin-only endpoints for RBAC.

Endpoints:
  PUT /api/v1/admin/users/{user_id}/role  — assign a role to a user (ADMIN only)
"""
from fastapi import APIRouter, Depends, status

from infrastructure.dependencies import get_current_user, require_role
from infrastructure.uow import UnitOfWork, get_uow
from core.models import Usuario
from usuarios.role_schemas import AssignRoleRequest, AssignRoleResponse
from usuarios.role_service import RoleService

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-roles"])


@router.put(
    "/{user_id}/role",
    response_model=AssignRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign a role to a user",
    description=(
        "Replaces the current role(s) of a user with the specified role. "
        "Only ADMIN can call this endpoint. "
        "Returns 409 if the target user is the last ADMIN and the new role is not ADMIN. "
        "Returns 404 if the user does not exist. "
        "Returns 422 if the role name is invalid."
    ),
    responses={
        200: {"description": "Role assigned successfully"},
        403: {"description": "Insufficient permissions — ADMIN role required"},
        404: {"description": "User not found"},
        409: {"description": "Conflict — would remove the last admin"},
        422: {"description": "Invalid role name"},
    },
)
async def assign_role(
    user_id: int,
    body: AssignRoleRequest,
    current_user: Usuario = Depends(get_current_user),
    _: None = Depends(require_role(["ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> AssignRoleResponse:
    """
    Assign a role to a user (ADMIN only).

    - **user_id**: Primary key of the target user
    - **rol_nombre**: One of ADMIN, STOCK, PEDIDOS, CLIENT

    The operation replaces all current roles with the specified role.
    Assigning the same role the user already has is idempotent (HTTP 200, no error).
    """
    async with uow:
        return await RoleService.assign_role(uow, user_id, body.rol_nombre)
