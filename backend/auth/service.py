"""
Auth service — business logic for user registration, login, and token refresh.

Pattern: Service layer owns business rules; delegates persistence to UoW/repositories.
"""
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
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
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

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

    # 1. Lookup user by email — use selectinload to avoid async lazy-load error on .roles
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = (
        select(Usuario)
        .where(Usuario.email == str(data.email))
        .options(selectinload(Usuario.roles))
    )
    result = await uow.session.execute(stmt)
    usuario = result.scalar_one_or_none()

    if usuario is None:
        # 2a. User not found: still run bcrypt to prevent timing attacks
        verify_password(data.password, DUMMY_HASH)
        raise invalid_credentials

    # 2b. User found: verify password against stored hash
    if not verify_password(data.password, usuario.hashed_password):
        raise invalid_credentials

    # 2c. Account must be active (soft-ban check — 403, not 401, to distinguish from bad creds)
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Forbidden",
                "status": 403,
                "detail": "Cuenta desactivada",
            },
        )

    # 3. Roles already eagerly loaded by selectinload above
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
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

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


async def logout_user(data: RefreshRequest, uow: UnitOfWork) -> None:
    """
    Revoke a refresh token, terminating the user's session server-side.

    Security flow:
    1. Look up the token row by the raw token string.
    2. If NOT found → counterfeit/never issued → 401.
    3. If found and revoked_at IS NOT NULL → already revoked; return None (idempotent 204).
    4. If found and revoked_at IS NULL → set revoked_at = now() and persist.
    5. Return None (router returns 204 No Content).

    Args:
        data: RefreshRequest containing the refresh_token string.
        uow: Unit of Work — caller must use as async context manager.

    Returns:
        None (HTTP 204 No Content).

    Raises:
        HTTPException 401 if the token is not found in the database.
    """
    # 1. Look up the token row
    token_record = await uow.refresh_tokens.find_by(token=data.refresh_token)

    # 2. Token not in DB — counterfeit or never issued
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Token already revoked — idempotent 204, do nothing
    if token_record.revoked_at is not None:
        return None

    # 4. Token is active — revoke it now
    token_record.revoked_at = datetime.utcnow()
    await uow.refresh_tokens.update(token_record)

    # 5. Return None → router returns 204 No Content
    return None


async def refresh_token_service(data: RefreshRequest, uow: UnitOfWork) -> TokenResponse:
    """
    Rotate a refresh token and return a new token pair.

    Security flow:
    1. Look up the token row by the raw JWT string.
    2. If NOT found → counterfeit/never issued → 401.
    3. If found but revoked_at IS NOT NULL → replay attack detected:
       revoke ALL tokens for that user and return 401.
    4. If found but expires_at < now() → expired → 401.
    5. Valid path: revoke old token, create new RefreshToken, issue new pair.

    Args:
        data: RefreshRequest containing the refresh_token string.
        uow: Unit of Work — caller must use as async context manager.

    Returns:
        TokenResponse with new access_token and refresh_token.

    Raises:
        HTTPException 401 for any validation failure.
    """
    now = datetime.utcnow()

    # 1. Look up the token row
    token_record = await uow.refresh_tokens.find_by(token=data.refresh_token)

    # 2. Token not in DB — counterfeit or already hard-deleted
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Token is already revoked → replay attack
    if token_record.revoked_at is not None:
        # Revoke ALL tokens for this user (family revocation)
        all_tokens = await uow.refresh_tokens.find_all_by(usuario_id=token_record.usuario_id)
        for t in all_tokens:
            if t.revoked_at is None:
                t.revoked_at = now
                await uow.refresh_tokens.update(t)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Replay attack detected — all sessions revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Token is expired (both expires_at and now are naive UTC)
    if token_record.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5a. Revoke old token
    token_record.revoked_at = now
    await uow.refresh_tokens.update(token_record)

    # 5b. Load user with roles eagerly to avoid async lazy-load error
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = (
        select(Usuario)
        .where(Usuario.id == token_record.usuario_id)
        .options(selectinload(Usuario.roles))
    )
    result = await uow.session.execute(stmt)
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = [r.nombre for r in usuario.roles] if usuario.roles else []

    # 5c. Issue new access token (stateless JWT)
    new_access_token = create_access_token(
        data={
            "sub": str(usuario.id),
            "email": usuario.email,
            "roles": roles,
        }
    )

    # 5d. Create and persist new refresh token
    new_refresh_token_str = create_refresh_token(usuario.id)
    new_expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    new_token_record = RefreshToken(
        usuario_id=usuario.id,
        token=new_refresh_token_str,
        expires_at=new_expires_at,
    )
    await uow.refresh_tokens.create(new_token_record)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token_str,
    )
