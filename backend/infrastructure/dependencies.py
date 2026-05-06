"""
FastAPI dependencies for authentication, JWT validation, and RBAC.

Provides:
- extract_token(): Parse Authorization header
- verify_token_dependency(): Validate JWT signature and expiration
- get_current_user(): Return current Usuario from token
- require_role(roles): Factory for role-based access control
"""

from typing import Optional, Callable
from datetime import datetime, timedelta
import os

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jwt import decode, encode, ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Usuario
from backend.infrastructure.uow import UnitOfWork, get_uow


# JWT Configuration (loaded from environment)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# HTTP Bearer authentication scheme
security = HTTPBearer()


async def extract_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """
    Extract JWT token from Authorization header.
    
    Args:
        credentials: HTTPAuthCredentials from FastAPI security
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException 401 if token missing or malformed
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def verify_token_dependency(token: str = Depends(extract_token)) -> dict:
    """
    Verify JWT token signature and expiration.
    
    Args:
        token: JWT token string from extract_token()
        
    Returns:
        Decoded JWT payload (dict)
        
    Raises:
        HTTPException 401 if token invalid or expired
    """
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    payload: dict = Depends(verify_token_dependency),
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
        HTTPException 404 if user not found
        HTTPException 403 if user is soft-deleted (eliminado_en IS NOT NULL)
    """
    user_id = int(payload.get("sub"))
    
    async with uow:
        user = await uow.usuarios.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    
    # Check if user is soft-deleted
    if user.eliminado_en is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )
    
    return user


async def require_role(*allowed_roles: str) -> Callable:
    """
    Factory function that returns a dependency for role-based access control.
    
    Usage in route:
        @app.post("/api/v1/usuarios")
        async def create_user(
            user_create: UserCreateSchema,
            current_user: Usuario = Depends(get_current_user),
            _ = Depends(require_role("ADMIN"))
        ):
            ...
    
    Args:
        allowed_roles: One or more role names (ADMIN, STOCK, PEDIDOS, CLIENT)
        
    Returns:
        Async dependency function for FastAPI
        
    Raises:
        HTTPException 403 if user's role not in allowed_roles
    """
    async def check_role(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        """Check if current user has one of the allowed roles."""
        # current_user.rol is a Rol entity, need to check rol.nombre
        if current_user.rol is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )
        
        if current_user.rol.nombre not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.rol.nombre}' not authorized. Required: {', '.join(allowed_roles)}",
            )
        
        return current_user
    
    return check_role


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary with claims to encode (should include "sub" for user_id)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
