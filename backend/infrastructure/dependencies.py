"""
FastAPI dependencies for authentication, JWT validation, and RBAC.

Provides:
- extract_token(): Parse Authorization header
- verify_token_dependency(): Validate JWT signature and expiration
- get_current_user(): Return current Usuario from token
- require_role(roles): Factory for role-based access control
"""

from typing import Optional, Callable, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Usuario
from core.security import verify_token, extract_token_from_header
from core.database import get_db
from infrastructure.uow import UnitOfWork, get_uow


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
    uow: UnitOfWork = Depends(get_uow),
) -> Usuario:
    """
    Get current authenticated user from JWT token.
    
    Args:
        payload: Decoded JWT payload from verify_token_dependency()
        uow: UnitOfWork for database access
        
    Returns:
        Current Usuario entity (fetched from database)
        
    Raises:
        HTTPException 401 if user not found
        HTTPException 403 if user is soft-deleted (eliminado_en IS NOT NULL)
    """
    user_id = int(payload.get("sub"))
    
    async with uow:
        user = await uow.usuarios.get_by_id(user_id)
    
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
        """Check if current user has one of the allowed roles."""
        if current_user.rol is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )
        
        if current_user.rol.nombre not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
    
    return check_role
