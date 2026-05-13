"""
Perfil router — authenticated user profile endpoints.

Endpoints (all require valid JWT via get_current_user):
  GET  /perfil              — return current user's profile
  PUT  /perfil              — update nombre and/or telefono
  POST /perfil/cambiar-password — change password + revoke all refresh tokens

Architecture note:
  This router is pure HTTP surface. All business logic lives in perfil_service.py.
  response_model is explicit on every endpoint (project convention).
"""
from fastapi import APIRouter, Depends

from core.dependencies import get_current_user
from core.models import Usuario
from infrastructure.uow import UnitOfWork, get_uow
from usuarios.perfil_schemas import CambiarPasswordRequest, PerfilUpdate
from usuarios.perfil_service import cambiar_password, get_perfil, update_perfil
from usuarios.schemas import UsuarioResponse

router = APIRouter(prefix="/perfil", tags=["Perfil"])


@router.get(
    "",
    response_model=UsuarioResponse,
    status_code=200,
    summary="Get authenticated user's profile",
    description=(
        "Returns the public profile of the currently authenticated user. "
        "Does not expose hashed_password or eliminado_en."
    ),
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Missing or invalid JWT"},
    },
)
async def get_perfil_endpoint(
    current_user: Usuario = Depends(get_current_user),
) -> UsuarioResponse:
    """Return the authenticated user's profile data."""
    return await get_perfil(current_user)


@router.put(
    "",
    response_model=UsuarioResponse,
    status_code=200,
    summary="Update authenticated user's profile",
    description=(
        "Updates nombre and/or telefono of the authenticated user. "
        "At least one field must be provided (422 otherwise). "
        "HTML tags are stripped from nombre."
    ),
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Missing or invalid JWT"},
        422: {"description": "Validation error — at least one field required"},
    },
)
async def update_perfil_endpoint(
    data: PerfilUpdate,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UsuarioResponse:
    """Partially update the authenticated user's profile."""
    async with uow:
        return await update_perfil(current_user, data, uow)


@router.post(
    "/cambiar-password",
    response_model=None,
    status_code=204,
    summary="Change authenticated user's password",
    description=(
        "Validates the current password, hashes the new one, and revokes "
        "ALL active refresh tokens for this user (RN-AU04). "
        "Returns 204 No Content on success."
    ),
    responses={
        204: {"description": "Password changed and sessions revoked"},
        400: {"description": "Incorrect current password (RFC 7807)"},
        401: {"description": "Missing or invalid JWT"},
        422: {
            "description": (
                "Validation error — password too short or "
                "nueva_password equals password_actual"
            )
        },
    },
)
async def cambiar_password_endpoint(
    data: CambiarPasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    """Change password and revoke all active refresh tokens."""
    async with uow:
        await cambiar_password(current_user, data, uow)
