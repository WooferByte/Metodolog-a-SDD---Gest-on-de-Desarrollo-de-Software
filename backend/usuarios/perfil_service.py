"""
Business logic for perfil (user profile) endpoints.

Architecture: Router → Service → UoW → Repository → Model
  - This service never calls session.commit() directly.
  - The UoW context manager handles commit/rollback automatically.
  - HTTPException is raised here (not in the router, not in repositories).
"""
from datetime import datetime

from fastapi import HTTPException, status

from core.models import Usuario
from core.security import hash_password, verify_password
from infrastructure.uow import UnitOfWork
from usuarios.perfil_schemas import CambiarPasswordRequest, PerfilUpdate
from usuarios.schemas import UsuarioResponse


async def get_perfil(current_user: Usuario) -> UsuarioResponse:
    """
    Return UsuarioResponse for the authenticated user.

    No database call is needed — the user is already loaded by the
    get_current_user() dependency.

    Args:
        current_user: Authenticated Usuario from JWT dependency.

    Returns:
        UsuarioResponse with all public fields.
    """
    return UsuarioResponse.model_validate(current_user)


async def update_perfil(
    current_user: Usuario,
    data: PerfilUpdate,
    uow: UnitOfWork,
) -> UsuarioResponse:
    """
    Apply partial update to the authenticated user's profile.

    Only non-None fields in data are patched. The UoW handles commit.

    Args:
        current_user: Authenticated Usuario from JWT dependency.
        data: PerfilUpdate with at least one non-None field.
        uow: Unit of Work — must be used inside `async with uow:` in the router.

    Returns:
        UsuarioResponse with updated fields.
    """
    if data.nombre is not None:
        current_user.nombre = data.nombre
    if data.telefono is not None:
        current_user.telefono = data.telefono

    await uow.usuarios.update(current_user)
    return UsuarioResponse.model_validate(current_user)


async def cambiar_password(
    current_user: Usuario,
    data: CambiarPasswordRequest,
    uow: UnitOfWork,
) -> None:
    """
    Change the authenticated user's password and revoke all active refresh tokens.

    Steps:
    1. Verify password_actual against the stored bcrypt hash.
    2. Hash nueva_password with bcrypt (cost configured globally in pwd_context).
    3. Persist the updated hashed_password via UoW.
    4. Revoke all active refresh tokens (RN-AU04).

    Args:
        current_user: Authenticated Usuario from JWT dependency.
        data: CambiarPasswordRequest — passwords pre-validated at schema level.
        uow: Unit of Work — must be used inside `async with uow:` in the router.

    Raises:
        HTTPException 400 (RFC 7807): password_actual is incorrect.

    Returns:
        None (router sends 204 No Content).
    """
    # Step 1 — verify current password
    if not verify_password(data.password_actual, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": "Contraseña actual incorrecta",
                "instance": "/api/v1/perfil/cambiar-password",
            },
        )

    # Step 2 — hash new password (bcrypt cost governed by pwd_context in core/security.py)
    current_user.hashed_password = hash_password(data.nueva_password)

    # Step 3 — persist updated user
    await uow.usuarios.update(current_user)

    # Step 4 — revoke all active refresh tokens (RN-AU04)
    tokens = await uow.refresh_tokens.find_all_by(usuario_id=current_user.id)
    for token in tokens:
        if token.revoked_at is None:
            token.revoked_at = datetime.utcnow()
            await uow.refresh_tokens.update(token)
