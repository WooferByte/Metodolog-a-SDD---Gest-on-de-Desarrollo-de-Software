"""
Categorias router — HTTP endpoints for product category management.

Architecture: Router → Service → UoW → Repository → Model

Endpoints:
    GET  /api/v1/categorias           — list flat, paginated, public
    GET  /api/v1/categorias/tree      — full recursive tree, public
    GET  /api/v1/categorias/{id}      — single category, public
    GET  /api/v1/categorias/{id}/subtree — subtree, public
    POST /api/v1/categorias           — create (STOCK or ADMIN)
    PUT  /api/v1/categorias/{id}      — update (STOCK or ADMIN)
    DELETE /api/v1/categorias/{id}    — soft-delete (STOCK or ADMIN)

IMPORTANT: GET /tree MUST be declared BEFORE GET /{categoria_id} in this
file. FastAPI matches routes in declaration order, so if /{categoria_id}
comes first, "tree" would be interpreted as an integer ID and cause a 422.
"""

from fastapi import APIRouter, Depends, Response, status

from categorias.schemas import CategoriaCreate, CategoriaResponse, CategoriaTreeItem, CategoriaUpdate
from categorias import service
from core.dependencies import require_role
from infrastructure.uow import UnitOfWork, get_uow

router = APIRouter(prefix="/categorias", tags=["Categorias"])


# ---------------------------------------------------------------------------
# Public GET endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[CategoriaResponse],
    summary="List categories (flat)",
    description=(
        "Returns a paginated flat list of active categories (excludes soft-deleted). "
        "Ordered by nombre. No authentication required."
    ),
)
async def list_categorias(
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
) -> list[CategoriaResponse]:
    """List all active categories with pagination."""
    async with uow:
        return await service.list_categorias(uow, skip=skip, limit=limit)


@router.get(
    "/tree",
    response_model=list[CategoriaTreeItem],
    summary="Full category tree",
    description=(
        "Returns the complete category hierarchy as a flat list. "
        "Each item includes a 'depth' field (0 = root). "
        "No authentication required."
    ),
)
async def get_tree(
    uow: UnitOfWork = Depends(get_uow),
) -> list[CategoriaTreeItem]:
    """Return the entire category forest as a flat list ordered by depth, nombre."""
    async with uow:
        return await service.get_tree(uow, root_id=None)


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Get category by ID",
    description="Return a single category by its primary key. No authentication required.",
)
async def get_categoria(
    categoria_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> CategoriaResponse:
    """Return a single Categoria or 404."""
    async with uow:
        return await service.get_categoria_by_id(uow, categoria_id)


@router.get(
    "/{categoria_id}/subtree",
    response_model=list[CategoriaTreeItem],
    summary="Category subtree",
    description=(
        "Return the subtree rooted at categoria_id as a flat list with depth. "
        "The root category itself is included (depth=0). "
        "Returns 404 if the root category does not exist. "
        "No authentication required."
    ),
)
async def get_subtree(
    categoria_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[CategoriaTreeItem]:
    """Return subtree rooted at categoria_id (root included, depth=0)."""
    async with uow:
        # Verify root exists before calling CTE (returns 404 if not)
        await service.get_categoria_by_id(uow, categoria_id)
        return await service.get_tree(uow, root_id=categoria_id)


# ---------------------------------------------------------------------------
# Protected POST / PUT / DELETE endpoints (STOCK or ADMIN)
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
    description="Create a new product category. Requires STOCK or ADMIN role.",
)
async def create_categoria(
    data: CategoriaCreate,
    _=Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> CategoriaResponse:
    """Create and persist a new Categoria."""
    async with uow:
        return await service.create_categoria(uow, data)


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a category",
    description=(
        "Partially update a category. Only provided fields are modified. "
        "Rejects updates that would create a hierarchy cycle. "
        "Requires STOCK or ADMIN role."
    ),
)
async def update_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    _=Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> CategoriaResponse:
    """Update an existing Categoria — partial update, cycle-safe."""
    async with uow:
        return await service.update_categoria(uow, categoria_id, data)


@router.delete(
    "/{categoria_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a category",
    description=(
        "Soft-delete a category (sets eliminado_en). "
        "Returns 409 if the category has active products linked to it. "
        "Requires STOCK or ADMIN role."
    ),
)
async def delete_categoria(
    categoria_id: int,
    _=Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Soft-delete a Categoria — guarded by active-products check."""
    async with uow:
        await service.delete_categoria(uow, categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
