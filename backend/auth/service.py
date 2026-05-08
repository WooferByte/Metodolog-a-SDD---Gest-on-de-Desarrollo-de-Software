"""
Auth service — business logic for user registration.

Pattern: Service layer owns business rules; delegates persistence to UoW/repositories.
"""
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status

from auth.schemas import RegisterRequest, TokenResponse
from core.models import Usuario, UsuarioRol, RefreshToken
from core.security import hash_password, create_access_token, create_refresh_token
from core.config import settings
from infrastructure.uow import UnitOfWork


async def register_user(data: RegisterRequest, uow: UnitOfWork) -> TokenResponse:
    """
    Register a new user and return authentication tokens.

    Steps:
    1. Hash password (bcrypt, cost >= 10)
    2. Create Usuario record
    3. Lookup CLIENT role from DB
    4. Assign CLIENT role via UsuarioRol pivot
    5. Create and store RefreshToken in DB
    6. Issue access token (stateless JWT, not stored)
    7. Return TokenResponse

    Args:
        data: Validated RegisterRequest (email, password, nombre, apellido?)
        uow: Unit of Work — caller must use as async context manager for atomicity

    Returns:
        TokenResponse with access_token, refresh_token, token_type

    Raises:
        HTTPException 500 if CLIENT role is missing from DB (seed data required)
        IntegrityError → auto-caught by error middleware → 409 if email is duplicate
    """
    # 1. Hash password
    hashed_pw = hash_password(data.password)

    # 2. Create Usuario
    nuevo_usuario = Usuario(
        email=str(data.email),
        hashed_password=hashed_pw,
        nombre=data.nombre,
        apellido=data.apellido,
        activo=True,
    )
    usuario = await uow.usuarios.create(nuevo_usuario)

    # 3. Lookup CLIENT role — must exist from seed data
    rol_client = await uow.roles.find_by(nombre="CLIENT")
    if rol_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLIENT role not found in database. Run seed script.",
        )

    # 4. Assign CLIENT role via pivot table
    usuario_rol = UsuarioRol(
        usuario_id=usuario.id,
        rol_id=rol_client.id,
    )
    await uow.usuario_roles.create(usuario_rol)

    # 5. Create refresh token string and persist it
    refresh_token_str = create_refresh_token(usuario.id)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    refresh_token_record = RefreshToken(
        usuario_id=usuario.id,
        token=refresh_token_str,
        expires_at=expires_at,
    )
    await uow.refresh_tokens.create(refresh_token_record)

    # 6. Issue access token (stateless — no DB write)
    access_token_str = create_access_token(
        data={
            "sub": str(usuario.id),
            "email": usuario.email,
            "roles": ["CLIENT"],
        }
    )

    # 7. Return response
    return TokenResponse(
        access_token=access_token_str,
        refresh_token=refresh_token_str,
    )
