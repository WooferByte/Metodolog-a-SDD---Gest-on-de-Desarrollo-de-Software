"""
Auth service — business logic for user registration and login.

Pattern: Service layer owns business rules; delegates persistence to UoW/repositories.
"""
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status

from auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from core.models import Usuario, UsuarioRol, RefreshToken
from core.security import hash_password, verify_password, create_access_token, create_refresh_token
from core.config import settings
from infrastructure.uow import UnitOfWork
from usuarios.schemas import UsuarioResponse

# Pre-computed bcrypt hash used when user is not found.
# Running verify_password against this prevents timing attacks by ensuring
# bcrypt work is done regardless of whether the email exists in the database.
DUMMY_HASH = "$2b$12$KixL1RJJ3DtDhvya0mIQNeKBJAHVKZ5XiMVIx9fLzN0sOr7kKhqGS"


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


async def login_user(data: LoginRequest, uow: UnitOfWork) -> TokenResponse:
    """
    Authenticate a user and return JWT tokens.

    Steps:
    1. Lookup user by email
    2. Always run bcrypt verification (prevents timing attacks)
    3. Raise generic 401 if user not found OR password incorrect (no enumeration)
    4. Build JWT access token payload: sub, email, roles
    5. Create and persist RefreshToken record (7-day expiry)
    6. Return TokenResponse with tokens + usuario

    Args:
        data: Validated LoginRequest (email, password)
        uow: Unit of Work — caller must use as async context manager for atomicity

    Returns:
        TokenResponse with access_token, refresh_token, token_type, usuario

    Raises:
        HTTPException 401 with generic "Invalid credentials" for any auth failure
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Lookup user by email
    usuario = await uow.usuarios.find_by(email=str(data.email))

    if usuario is None:
        # 2a. User not found: still run bcrypt to prevent timing attacks
        verify_password(data.password, DUMMY_HASH)
        raise invalid_credentials

    # 2b. User found: verify password against stored hash
    if not verify_password(data.password, usuario.hashed_password):
        raise invalid_credentials

    # 3. Fetch user's roles for token payload
    roles = [r.nombre for r in usuario.roles] if usuario.roles else []

    # 4. Build and sign JWT access token
    access_token_str = create_access_token(
        data={
            "sub": str(usuario.id),
            "email": usuario.email,
            "roles": roles,
        }
    )

    # 5. Create refresh token and persist it
    refresh_token_str = create_refresh_token(usuario.id)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    refresh_token_record = RefreshToken(
        usuario_id=usuario.id,
        token=refresh_token_str,
        expires_at=expires_at,
    )
    await uow.refresh_tokens.create(refresh_token_record)

    # 6. Return token response with user info
    return TokenResponse(
        access_token=access_token_str,
        refresh_token=refresh_token_str,
        usuario=UsuarioResponse.model_validate(usuario),
    )
