"""
Ingredientes router — HTTP endpoints for ingredient management.

Architecture: Router → Service → UoW → Repository → Model

Endpoints:
    GET  /api/v1/ingredientes           — list, paginated, optional ?es_alergeno filter, public
    GET  /api/v1/ingredientes/{id}      — single ingredient, public
    POST /api/v1/ingredientes           — create (STOCK or ADMIN)
    PUT  /api/v1/ingredientes/{id}      — update (STOCK or ADMIN)
    DELETE /api/v1/ingredientes/{id}    — soft-delete (STOCK or ADMIN)
"""

from typing import Optional

from fastapi import APIRouter, Depends, Response, status

from ingredientes.schemas import IngredienteCreate, IngredienteResponse, IngredienteUpdate
from ingredientes import service
from core.dependencies import require_role
from infrastructure.uow import UnitOfWork, get_uow

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])


# ---------------------------------------------------------------------------
# Public GET endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[IngredienteResponse],
    summary="List ingredients",
    description=(
        "Returns a paginated list of active ingredients (excludes soft-deleted). "
        "Optionally filter by allergen status with ?es_alergeno=true or ?es_alergeno=false. "
        "No authentication required."
    ),
)
async def list_ingredientes(
    skip: int = 0,
    limit: int = 100,
    es_alergeno: Optional[bool] = None,
    uow: UnitOfWork = Depends(get_uow),
) -> list[IngredienteResponse]:
    """List all active ingredients with optional allergen filter and pagination."""
    async with uow:
        return await service.list_ingredientes(uow, skip=skip, limit=limit, es_alergeno=es_alergeno)


@router.get(
    "/{ingrediente_id}",
    response_model=IngredienteResponse,
    summary="Get ingredient by ID",
    description="Return a single ingredient by its primary key. No authentication required.",
)
async def get_ingrediente(
    ingrediente_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> IngredienteResponse:
    """Return a single Ingrediente or 404."""
    async with uow:
        return await service.get_ingrediente_by_id(uow, ingrediente_id)


# ---------------------------------------------------------------------------
# Protected POST / PUT / DELETE endpoints (STOCK or ADMIN)
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=IngredienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ingredient",
    description="Create a new ingredient. Requires STOCK or ADMIN role.",
)
async def create_ingrediente(
    data: IngredienteCreate,
    _=Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> IngredienteResponse:
    """Create and persist a new Ingrediente."""
    async with uow:
        return await service.create_ingrediente(uow, data)


@router.put(
    "/{ingrediente_id}",
    response_model=IngredienteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an ingredient",
    description=(
        "Partially update an ingredient. Only provided fields are modified. "
        "Requires STOCK or ADMIN role."
    ),
)
async def update_ingrediente(
    ingrediente_id: int,
    data: IngredienteUpdate,
    _=Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> IngredienteResponse:
    """Update an existing Ingrediente — partial update."""
    async with uow:
        return await service.update_ingrediente(uow, ingrediente_id, data)


@router.delete(
    "/{ingrediente_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an ingredient",
    description=(
        "Soft-delete an ingredient (sets eliminado_en). "
        "Returns 409 if the ingredient is used by active products. "
        "Requires STOCK or ADMIN role."
    ),
)
async def delete_ingrediente(
    ingrediente_id: int,
    _=Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Soft-delete an Ingrediente — guarded by active-products check."""
    async with uow:
        await service.delete_ingrediente(uow, ingrediente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
