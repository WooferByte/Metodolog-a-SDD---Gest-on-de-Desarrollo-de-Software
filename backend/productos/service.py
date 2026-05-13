"""
Product service — business logic layer for productos module.

Architecture: Router → Service → UoW → Repository → Model
- This module is the ONLY layer that raises HTTPException.
- Never calls session.commit() directly (handled by UoW).
- Validates business rules: existence checks, role guards for incluir_eliminados.
"""

from typing import Optional

from fastapi import HTTPException, status

from core.models import Producto, Usuario
from infrastructure.uow import UnitOfWork
from productos.schemas import ProductoCreate, ProductoUpdate, ProductoStockUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_404(uow: UnitOfWork, producto_id: int) -> Producto:
    """
    Return Producto by ID or raise HTTPException 404.

    Args:
        uow: Unit of Work providing repository access.
        producto_id: Primary key to look up.

    Returns:
        Producto if found and not soft-deleted.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    producto = await uow.productos.get_by_id(producto_id)
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": f"Producto {producto_id} not found",
            },
        )
    return producto


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def list_productos(
    uow: UnitOfWork,
    skip: int = 0,
    limit: int = 100,
    incluir_eliminados: bool = False,
    current_user: Optional[Usuario] = None,
) -> list[Producto]:
    """
    Return a paginated list of products ordered by nombre.

    If incluir_eliminados=True, enforces that the caller has STOCK or ADMIN role.

    Args:
        uow: Unit of Work.
        skip: Pagination offset.
        limit: Maximum records to return.
        incluir_eliminados: If True, include soft-deleted products (RN-CA10 — requires STOCK or ADMIN).
        current_user: Authenticated user (may be None for public requests).

    Returns:
        List of Producto instances.

    Raises:
        HTTPException 403 if incluir_eliminados=True and user lacks STOCK/ADMIN role.
    """
    if incluir_eliminados:
        # RN-CA10: only STOCK or ADMIN may see deleted products
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": "Authentication required to include deleted products",
                },
            )
        user_roles = {r.nombre for r in current_user.roles}
        if not user_roles.intersection({"STOCK", "ADMIN"}):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Forbidden",
                    "status": 403,
                    "detail": "No tenés el rol requerido para ver productos eliminados",
                },
            )

    return await uow.productos.list_active(
        skip=skip,
        limit=limit,
        incluir_eliminados=incluir_eliminados,
    )


async def get_producto_by_id(
    uow: UnitOfWork,
    producto_id: int,
) -> Producto:
    """
    Return a single Producto by primary key.

    Args:
        uow: Unit of Work.
        producto_id: Product ID to retrieve.

    Returns:
        Producto if found and not soft-deleted.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    return await _get_or_404(uow, producto_id)


async def create_producto(
    uow: UnitOfWork,
    data: ProductoCreate,
) -> Producto:
    """
    Create a new product.

    Args:
        uow: Unit of Work.
        data: Validated ProductoCreate payload.

    Returns:
        Newly created Producto instance.
    """
    producto = Producto(**data.model_dump())
    await uow.productos.create(producto)
    return producto


async def update_producto(
    uow: UnitOfWork,
    producto_id: int,
    data: ProductoUpdate,
) -> Producto:
    """
    Partially update an existing product.

    Only non-None fields from data are applied.

    Args:
        uow: Unit of Work.
        producto_id: ID of the product to update.
        data: ProductoUpdate payload (all fields optional).

    Returns:
        Updated Producto instance.

    Raises:
        HTTPException 404 if producto_id does not exist.
    """
    producto = await _get_or_404(uow, producto_id)

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(producto, field, value)

    await uow.productos.update(producto)
    return producto


async def delete_producto(
    uow: UnitOfWork,
    producto_id: int,
) -> None:
    """
    Soft-delete a product.

    Args:
        uow: Unit of Work.
        producto_id: ID of the product to soft-delete.

    Raises:
        HTTPException 404 if producto_id does not exist.
    """
    await _get_or_404(uow, producto_id)
    await uow.productos.soft_delete(producto_id)


async def patch_stock(
    uow: UnitOfWork,
    producto_id: int,
    data: ProductoStockUpdate,
) -> Producto:
    """
    Update only the stock_cantidad of a product.

    Args:
        uow: Unit of Work.
        producto_id: ID of the product to update.
        data: ProductoStockUpdate payload with stock_cantidad >= 0.

    Returns:
        Updated Producto instance.

    Raises:
        HTTPException 404 if producto_id does not exist.
    """
    producto = await _get_or_404(uow, producto_id)
    producto.stock_cantidad = data.stock_cantidad
    await uow.productos.update(producto)
    return producto
