"""
Ingrediente service — business logic layer for ingredientes module.

Architecture: Router → Service → UoW → Repository → Model
- This module is the ONLY layer that raises HTTPException.
- Never calls session.commit() directly (handled by UoW).
- Validates business rules: existence checks, UNIQUE → 409, active-products guard on delete.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from ingredientes.schemas import IngredienteCreate, IngredienteUpdate
from core.models import Ingrediente
from infrastructure.uow import UnitOfWork


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_404(uow: UnitOfWork, ingrediente_id: int) -> Ingrediente:
    """
    Return Ingrediente by ID or raise HTTPException 404.

    Args:
        uow: Unit of Work providing repository access.
        ingrediente_id: Primary key to look up.

    Returns:
        Ingrediente if found and not soft-deleted.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    ingrediente = await uow.ingredientes.get_by_id(ingrediente_id)
    if ingrediente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": f"Ingrediente {ingrediente_id} not found",
            },
        )
    return ingrediente


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def list_ingredientes(
    uow: UnitOfWork,
    skip: int = 0,
    limit: int = 100,
    es_alergeno: Optional[bool] = None,
) -> list[Ingrediente]:
    """
    Return a paginated list of active ingredients, optionally filtered by allergen flag.

    Args:
        uow: Unit of Work.
        skip: Pagination offset.
        limit: Maximum records to return.
        es_alergeno: When None, returns all ingredients. When True/False, filters by flag.

    Returns:
        List of Ingrediente instances excluding soft-deleted.
    """
    if es_alergeno is None:
        return await uow.ingredientes.list_all(skip=skip, limit=limit)
    return await uow.ingredientes.list_by_alergeno(es_alergeno=es_alergeno, skip=skip, limit=limit)


async def get_ingrediente_by_id(
    uow: UnitOfWork,
    ingrediente_id: int,
) -> Ingrediente:
    """
    Return a single Ingrediente by primary key.

    Args:
        uow: Unit of Work.
        ingrediente_id: Ingredient ID to retrieve.

    Returns:
        Ingrediente if found.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    return await _get_or_404(uow, ingrediente_id)


async def create_ingrediente(
    uow: UnitOfWork,
    data: IngredienteCreate,
) -> Ingrediente:
    """
    Create a new ingredient.

    Args:
        uow: Unit of Work.
        data: Validated IngredienteCreate payload.

    Returns:
        Newly created Ingrediente instance.

    Raises:
        HTTPException 409 if nombre violates the unique constraint.
    """
    ingrediente = Ingrediente(**data.model_dump())
    try:
        await uow.ingredientes.create(ingrediente)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": "Ingredient name already exists",
            },
        )
    return ingrediente


async def update_ingrediente(
    uow: UnitOfWork,
    ingrediente_id: int,
    data: IngredienteUpdate,
) -> Ingrediente:
    """
    Partially update an existing ingredient.

    Only non-None fields from data are applied to the ingredient.

    Args:
        uow: Unit of Work.
        ingrediente_id: ID of the ingredient to update.
        data: IngredienteUpdate payload (all fields optional).

    Returns:
        Updated Ingrediente instance.

    Raises:
        HTTPException 404 if ingrediente_id does not exist.
        HTTPException 409 if the updated nombre violates the unique constraint.
    """
    ingrediente = await _get_or_404(uow, ingrediente_id)

    # Apply only non-None fields
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(ingrediente, field, value)

    try:
        await uow.ingredientes.update(ingrediente)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": "Ingredient name already exists",
            },
        )
    return ingrediente


async def delete_ingrediente(
    uow: UnitOfWork,
    ingrediente_id: int,
) -> None:
    """
    Soft-delete an ingredient.

    Refuses deletion if the ingredient is used by at least one active product
    linked via producto_ingrediente (products with eliminado_en IS NULL).

    Args:
        uow: Unit of Work.
        ingrediente_id: ID of the ingredient to soft-delete.

    Raises:
        HTTPException 404 if ingrediente_id does not exist.
        HTTPException 409 if the ingredient has active products.
    """
    # Verify ingredient exists
    await _get_or_404(uow, ingrediente_id)

    # Guard: active products
    if await uow.ingredientes.has_active_products(ingrediente_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": "Cannot delete ingredient used by active products",
            },
        )

    await uow.ingredientes.soft_delete(ingrediente_id)
