"""
FastAPI dependencies for authentication, JWT validation, and RBAC.

Provides:
- extract_token(): Parse Authorization header
- verify_token_dependency(): Validate JWT signature and expiration
- get_current_user(): Return current Usuario from token
- require_role(roles): Factory for role-based access control
"""

from typing import Optional, Callable, Any

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Usuario
from core.security import verify_token, extract_token_from_header
from core.database import get_db


async def extract_token(auth_header: Optional[str] = Header(None, alias="authorization")) -> str:
    """
    Extract JWT token from Authorization header.
    
    Expected format: "Bearer <token>"
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException 401 if token missing or malformed
    """
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return extract_token_from_header(auth_header)


async def verify_token_dependency(token: str = Depends(extract_token)) -> dict[str, Any]:
    """
    Verify JWT token signature and expiration.
    
    Args:
        token: JWT token string from extract_token()
        
    Returns:
        Decoded JWT payload (dict)
        
    Raises:
        HTTPException 401 if token invalid or expired
    """
    return verify_token(token)


async def get_current_user(
    payload: dict[str, Any] = Depends(verify_token_dependency),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Get current authenticated user from JWT token.

    Uses a direct session query with eager-loaded roles to avoid UoW atomicity issues.

    Args:
        payload: Decoded JWT payload from verify_token_dependency()
        session: AsyncSession for database access

    Returns:
        Current Usuario entity with roles eagerly loaded

    Raises:
        HTTPException 401 if token payload invalid or user not found
        HTTPException 403 if user is soft-deleted (eliminado_en IS NOT NULL)
    """
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(
        select(Usuario)
        .where(Usuario.id == int(user_id_str))
        .options(selectinload(Usuario.roles))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is soft-deleted
    if user.eliminado_en is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )

    return user


def require_role(allowed_roles: list[str]) -> Callable:
    """
    Factory function that returns a dependency for role-based access control.
    
    Usage in route:
        @app.post("/api/v1/usuarios")
        async def create_user(
            user_create: UserCreateSchema,
            current_user: Usuario = Depends(get_current_user),
            _ = Depends(require_role(["ADMIN"]))
        ):
            ...
    
    Args:
        allowed_roles: List of role names (ADMIN, STOCK, PEDIDOS, CLIENT)
        
    Returns:
        Async dependency function for FastAPI
        
    Raises:
        HTTPException 403 if user's role not in allowed_roles
    """
    async def check_role(current_user: Usuario = Depends(get_current_user)) -> None:
        """Check if current user has one of the allowed roles (N:M)."""
        role_names = {rol.nombre for rol in current_user.roles}
        if not role_names.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
    
    return check_role
