"""
FastAPI dependencies for authentication and role-based access control (RBAC).

Provides:
- get_current_user(): Return current Usuario from JWT token (401 if missing/invalid)
- require_role(roles): Factory that returns a Depends-compatible callable
  that validates the current user has at least one of the required roles (403 if not)

Architecture note:
  These dependencies live in core/ because they are cross-cutting concerns used
  by all routers. They delegate JWT verification to core/security.py and DB
  access to a raw AsyncSession (no UoW needed — read-only lookup).

Usage:
    from core.dependencies import get_current_user, require_role

    @router.get("/perfil", response_model=UsuarioResponse)
    async def get_perfil(
        current_user: Usuario = Depends(require_role(["CLIENT"]))
    ) -> UsuarioResponse:
        ...
"""

from typing import Any, Callable, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.models import Usuario
from core.security import extract_token_from_header, verify_token


# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------


async def _extract_token(
    authorization: Optional[str] = Header(None, alias="authorization"),
) -> str:
    """
    Parse the Authorization header and return the raw JWT string.

    Raises:
        HTTPException 401 if the header is absent or malformed.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return extract_token_from_header(authorization)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------


async def _verify_token(
    token: str = Depends(_extract_token),
) -> dict[str, Any]:
    """
    Verify the JWT signature and standard claims.

    Returns:
        Decoded payload dict.

    Raises:
        HTTPException 401 if the token is invalid or expired.
    """
    return verify_token(token)


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


async def get_current_user(
    payload: dict[str, Any] = Depends(_verify_token),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Return the authenticated Usuario for the current request.

    Eagerly loads the ``roles`` relationship so role membership can be checked
    without additional queries (avoids async lazy-load errors).

    Args:
        payload: Decoded JWT payload (from _verify_token).
        session: AsyncSession provided by FastAPI DI.

    Returns:
        Current Usuario instance with roles eagerly loaded.

    Raises:
        HTTPException 401 if ``sub`` is absent from payload or user is not found.
        HTTPException 403 if the user account has been soft-deleted.
    """
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = (
        select(Usuario)
        .where(Usuario.id == int(user_id_str))
        .options(selectinload(Usuario.roles))
    )
    result = await session.execute(stmt)
    user: Optional[Usuario] = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.eliminado_en is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "about:blank",
                "title": "Forbidden",
                "status": 403,
                "detail": "User account has been deleted",
            },
        )

    return user


# ---------------------------------------------------------------------------
# Role guard — factory
# ---------------------------------------------------------------------------


def require_role(roles: list[str]) -> Callable:
    """
    Dependency factory for role-based access control.

    Returns a FastAPI-compatible async dependency that:
      1. Calls get_current_user (raises 401 if token is missing/invalid).
      2. Checks that the user holds at least one of the specified roles.
      3. Raises HTTP 403 (RFC 7807) if none of the roles match.
      4. Returns the Usuario so callers can use it directly.

    Usage — single dependency replaces get_current_user:

        @router.get("/perfil", response_model=UsuarioResponse)
        async def get_perfil(
            current_user: Usuario = Depends(require_role(["CLIENT"]))
        ) -> UsuarioResponse:
            ...

    Usage — guard only (result discarded):

        @router.delete("/{id}")
        async def delete(
            id: int,
            _: None = Depends(require_role(["ADMIN"])),
        ) -> None:
            ...

    Args:
        roles: List of role names that are allowed (e.g. ["ADMIN", "STOCK"]).

    Returns:
        Async dependency callable compatible with FastAPI ``Depends()``.
    """

    async def _check(
        current_user: Usuario = Depends(get_current_user),
    ) -> Usuario:
        user_roles = {r.nombre for r in current_user.roles}
        if not user_roles.intersection(set(roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": "No tenés el rol requerido",
                },
            )
        return current_user

    return _check
