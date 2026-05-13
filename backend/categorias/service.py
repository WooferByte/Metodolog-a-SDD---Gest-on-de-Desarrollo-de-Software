"""
Category service — business logic layer for categorias module.

Architecture: Router → Service → UoW → Repository → Model
- This module is the ONLY layer that raises HTTPException.
- Never calls session.commit() directly (handled by UoW).
- Validates business rules: existence checks, cycle detection, product guards.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from categorias.schemas import CategoriaCreate, CategoriaUpdate, CategoriaTreeItem
from core.models import Categoria
from infrastructure.uow import UnitOfWork


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_404(uow: UnitOfWork, categoria_id: int) -> Categoria:
    """
    Return Categoria by ID or raise HTTPException 404.

    Args:
        uow: Unit of Work providing repository access.
        categoria_id: Primary key to look up.

    Returns:
        Categoria if found and not soft-deleted.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    categoria = await uow.categorias.get_by_id(categoria_id)
    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": f"Categoria {categoria_id} not found",
            },
        )
    return categoria


async def _would_create_cycle(
    uow: UnitOfWork, child_id: int, proposed_padre_id: int
) -> bool:
    """
    Walk the ancestor chain of proposed_padre_id to detect cycles.

    A cycle exists when child_id appears anywhere in the ancestor chain of
    proposed_padre_id (including proposed_padre_id itself).

    Algorithm:
        - Start at proposed_padre_id and follow padre_id links upward.
        - If we encounter child_id → cycle detected → return True.
        - A visited set guards against already-corrupted data with existing cycles.

    Args:
        uow: Unit of Work providing repository access.
        child_id: ID of the category being updated.
        proposed_padre_id: The new padre_id value to validate.

    Returns:
        True if assigning proposed_padre_id would create a cycle.
    """
    current_id: Optional[int] = proposed_padre_id
    visited: set[int] = set()

    while current_id is not None:
        if current_id == child_id:
            return True  # cycle found
        if current_id in visited:
            break  # guard against existing corrupt data
        visited.add(current_id)
        ancestor = await uow.categorias.get_by_id(current_id)
        if ancestor is None:
            break
        current_id = ancestor.padre_id

    return False


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def list_categorias(
    uow: UnitOfWork,
    skip: int = 0,
    limit: int = 100,
) -> list[Categoria]:
    """
    Return a flat paginated list of active categories, ordered by nombre.

    Args:
        uow: Unit of Work.
        skip: Pagination offset.
        limit: Maximum records to return (capped at 1000 by BaseRepository).

    Returns:
        List of Categoria instances excluding soft-deleted.
    """
    return await uow.categorias.list_all(skip=skip, limit=limit)


async def get_categoria_by_id(
    uow: UnitOfWork,
    categoria_id: int,
) -> Categoria:
    """
    Return a single Categoria by primary key.

    Args:
        uow: Unit of Work.
        categoria_id: Category ID to retrieve.

    Returns:
        Categoria if found.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    return await _get_or_404(uow, categoria_id)


async def get_tree(
    uow: UnitOfWork,
    root_id: Optional[int] = None,
) -> list[CategoriaTreeItem]:
    """
    Return the full category tree (or a subtree) as a flat list with depth.

    Each item in the returned list includes the depth field indicating how
    many levels below the root the category sits (0 = root).

    Args:
        uow: Unit of Work.
        root_id: If None, return the complete forest. If set, return the
                 subtree rooted at root_id (root category + all descendants).

    Returns:
        List of CategoriaTreeItem, ordered by depth then nombre.
    """
    rows = await uow.categorias.get_tree(root_id=root_id)
    return [CategoriaTreeItem(**row) for row in rows]


async def create_categoria(
    uow: UnitOfWork,
    data: CategoriaCreate,
) -> Categoria:
    """
    Create a new product category.

    Validates that the padre_id (if provided) exists.
    No cycle-check needed on create: a brand-new category has no children,
    so it cannot participate in a cycle.

    Args:
        uow: Unit of Work.
        data: Validated CategoriaCreate payload.

    Returns:
        Newly created Categoria instance.

    Raises:
        HTTPException 404 if padre_id does not exist.
        HTTPException 409 if nombre violates the unique constraint.
    """
    # Validate parent exists (only if padre_id supplied)
    if data.padre_id is not None:
        await _get_or_404(uow, data.padre_id)

    categoria = Categoria(**data.model_dump())
    try:
        await uow.categorias.create(categoria)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": "Category name already exists",
            },
        )
    return categoria


async def update_categoria(
    uow: UnitOfWork,
    categoria_id: int,
    data: CategoriaUpdate,
) -> Categoria:
    """
    Partially update an existing category.

    Only non-None fields from data are applied to the category.

    Cycle-detection:
        If padre_id changes to a non-None value, verify that the proposed
        padre_id is not a descendant of categoria_id (which would close a cycle).

    Args:
        uow: Unit of Work.
        categoria_id: ID of the category to update.
        data: CategoriaUpdate payload (all fields optional).

    Returns:
        Updated Categoria instance.

    Raises:
        HTTPException 404 if categoria_id or new padre_id does not exist.
        HTTPException 400 if the update would create a hierarchy cycle.
        HTTPException 409 if the updated nombre violates the unique constraint.
    """
    categoria = await _get_or_404(uow, categoria_id)

    # Cycle detection: only when padre_id is explicitly provided and non-None
    if data.padre_id is not None:
        # Reject self-reference immediately
        if data.padre_id == categoria_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "about:blank",
                    "title": "Bad Request",
                    "status": 400,
                    "detail": "Cycle detected in category hierarchy",
                },
            )
        if await _would_create_cycle(uow, categoria_id, data.padre_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "about:blank",
                    "title": "Bad Request",
                    "status": 400,
                    "detail": "Cycle detected in category hierarchy",
                },
            )
        # Verify new parent exists
        await _get_or_404(uow, data.padre_id)

    # Apply only non-None fields
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(categoria, field, value)

    try:
        await uow.categorias.update(categoria)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": "Category name already exists",
            },
        )
    return categoria


async def delete_categoria(
    uow: UnitOfWork,
    categoria_id: int,
) -> None:
    """
    Soft-delete a category.

    Refuses deletion if the category has at least one active product linked
    via producto_categoria (products with eliminado_en IS NULL).

    Args:
        uow: Unit of Work.
        categoria_id: ID of the category to soft-delete.

    Raises:
        HTTPException 404 if categoria_id does not exist.
        HTTPException 409 if the category has active products.
    """
    # Verify category exists
    await _get_or_404(uow, categoria_id)

    # Guard: active products
    if await uow.categorias.has_active_products(categoria_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": "Cannot delete category with active products",
            },
        )

    await uow.categorias.soft_delete(categoria_id)
