"""
FastAPI dependencies for authentication and authorization.

Provides:
- get_current_user(): Extracts and validates JWT, returns Usuario
- require_role(): Factory for role-based access control (RBAC)
- Token extraction and validation
"""
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import Usuario
from core.security import extract_token_from_header, verify_token
from .uow import UnitOfWork


# ============================================================================
# JWT Token Extraction & Validation
# ============================================================================


async def extract_token(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        str: Extracted JWT token
        
    Raises:
        HTTPException: 401 if header missing or malformed
    """
    return extract_token_from_header(authorization)


async def verify_token_dependency(token: str = Depends(extract_token)) -> dict:
    """
    Verify JWT token and extract payload.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: 401 if token invalid or expired
    """
    return verify_token(token)


# ============================================================================
# Current User Dependency
# ============================================================================


async def get_current_user(
    token_payload: dict = Depends(verify_token_dependency),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Get current authenticated user from JWT token.
    
    Performs:
    - JWT token extraction and validation
    - User lookup by ID from database
    - Soft-delete check (fails if user.eliminado_en is not None)
    
    Args:
        token_payload: Decoded JWT token payload
        db: Database session
        
    Returns:
        Usuario: Current authenticated user entity
        
    Raises:
        HTTPException: 401 if token invalid
        HTTPException: 401 if user not found
        HTTPException: 403 if user is soft-deleted
        
    Usage:
        @app.get("/api/v1/perfil")
        async def get_profile(current_user: Usuario = Depends(get_current_user)):
            return {"email": current_user.email, "nombre": current_user.nombre}
    """
    # Extract user ID from token payload
    user_id: Optional[int] = token_payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing user ID (sub claim)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert user_id to int if it's a string
    try:
        user_id = int(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Look up user in database
    uow = UnitOfWork(db)
    async with uow:
        user = await uow.usuarios.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is soft-deleted
    if user.eliminado_en is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated",
        )
    
    return user


# ============================================================================
# Role-Based Access Control (RBAC) Factory
# ============================================================================


def require_role(required_roles: list[str]) -> Callable:
    """
    Factory function for role-based route protection.
    
    Returns a FastAPI dependency that validates current user has at least
    one of the specified roles.
    
    Args:
        required_roles: List of role names (e.g., ["ADMIN", "STOCK"])
        
    Returns:
        Callable: Async dependency function
        
    Raises:
        HTTPException: 403 Forbidden if user lacks required role
        
    Usage:
        @app.post("/api/v1/categorias")
        async def create_category(
            data: CreateCategoryRequest,
            current_user: Usuario = Depends(get_current_user),
            _ = Depends(require_role(["ADMIN", "STOCK"]))
        ):
            # Only ADMIN or STOCK users can reach here
            pass
        
        @app.delete("/api/v1/usuarios/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: Usuario = Depends(get_current_user),
            _ = Depends(require_role(["ADMIN"]))
        ):
            # Only ADMIN can reach here
            pass
    """
    
    async def check_role(current_user: Usuario = Depends(get_current_user)) -> bool:
        """
        Validate current user has at least one required role.
        
        Args:
            current_user: Current authenticated user from get_current_user()
            
        Returns:
            bool: True if user has required role
            
        Raises:
            HTTPException: 403 Forbidden if role not matched
        """
        if current_user.rol is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role",
            )
        
        # Check if user's role is in required roles list
        if current_user.rol.nombre not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.rol.nombre}' not authorized. "
                       f"Required one of: {', '.join(required_roles)}",
            )
        
        return True
    
    return check_role


# ============================================================================
# Unit of Work Dependency
# ============================================================================


async def get_uow(db: AsyncSession = Depends(get_db)) -> UnitOfWork:
    """
    FastAPI dependency for Unit of Work.
    
    Returns:
        UnitOfWork: Configured for request-scoped transaction
        
    Usage:
        @app.post("/api/v1/pedidos")
        async def create_order(
            data: CreateOrderRequest,
            current_user: Usuario = Depends(get_current_user),
            uow: UnitOfWork = Depends(get_uow),
        ):
            async with uow:
                # Multiple repository operations in single transaction
                new_order = Pedido(usuario_id=current_user.id, ...)
                await uow.pedidos.create(new_order)
                
                # Auto-commit on exit if no exception
                # Auto-rollback if exception
    """
    return UnitOfWork(db)
