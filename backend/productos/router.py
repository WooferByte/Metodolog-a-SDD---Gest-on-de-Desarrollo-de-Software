"""
Productos router — HTTP endpoints for product management.

Architecture: Router → Service → UoW → Repository → Model

Endpoints:
    GET  /api/v1/productos                                  — paginated list, public; ?incluir_eliminados=true requires STOCK/ADMIN; ?excluirAlergenos=1,3,7 filters by allergens
    GET  /api/v1/productos/{id}/categorias                  — list product categories, public
    PUT  /api/v1/productos/{id}/categorias                  — replace category set (STOCK or ADMIN)
    DELETE /api/v1/productos/{id}/categorias/{cat_id}       — remove one category (STOCK or ADMIN)
    GET  /api/v1/productos/{id}/ingredientes                — list product ingredients, public
    PUT  /api/v1/productos/{id}/ingredientes                — replace ingredient set (STOCK or ADMIN)
    DELETE /api/v1/productos/{id}/ingredientes/{ing_id}     — remove one ingredient (STOCK or ADMIN)
    GET  /api/v1/productos/{id}                             — single product, public
    POST /api/v1/productos                                  — create (STOCK or ADMIN)
    PUT  /api/v1/productos/{id}                             — full update (STOCK or ADMIN)
    DELETE /api/v1/productos/{id}                           — soft-delete (STOCK or ADMIN)
    PATCH /api/v1/productos/{id}/stock                      — stock-only update (STOCK or ADMIN)

IMPORTANT: Sub-resource paths (/{producto_id}/categorias, /{producto_id}/ingredientes,
/{producto_id}/stock) MUST be declared BEFORE /{producto_id} to avoid FastAPI matching
string literals as integer IDs and returning 422.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from core.dependencies import get_current_user, require_role
from core.models import Usuario
from core.security import extract_token_from_header, verify_token
from infrastructure.uow import UnitOfWork, get_uow
from productos import service
from productos.schemas import (
    CategoriaCompacta,
    IngredienteCompacto,
    ProductoCategoriaSetRequest,
    ProductoCreate,
    ProductoIngredienteSetRequest,
    ProductoResponse,
    ProductoStockUpdate,
    ProductoUpdate,
)


async def get_optional_user(
    authorization: Optional[str] = Header(None, alias="authorization"),
    uow: UnitOfWork = Depends(get_uow),
) -> Optional[Usuario]:
    """
    Return the current Usuario if a valid Bearer token is present, else None.

    Used for endpoints that are public but optionally authenticated
    (e.g., list with incluir_eliminados=true requires STOCK/ADMIN).
    """
    if not authorization:
        return None
    try:
        token = extract_token_from_header(authorization)
        payload = verify_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Usuario)
            .where(Usuario.id == int(user_id_str))
            .options(selectinload(Usuario.roles))
        )
        result = await uow.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None or user.eliminado_en is not None:
            return None
        return user
    except Exception:
        return None

router = APIRouter(prefix="/productos", tags=["Productos"])


# ---------------------------------------------------------------------------
# Public GET endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[ProductoResponse],
    summary="List products",
    description=(
        "Returns a paginated list of active products (excludes soft-deleted). "
        "Add ?incluir_eliminados=true with STOCK or ADMIN role to see all products. "
        "Add ?excluirAlergenos=1,3,7 (comma-separated ingredient IDs, max 50) to filter out "
        "products containing any of those allergen ingredients. "
        "No authentication required for the default list."
    ),
)
async def list_productos(
    skip: int = 0,
    limit: int = 100,
    incluir_eliminados: bool = False,
    excluirAlergenos: Optional[str] = Query(
        default=None,
        description="Comma-separated list of ingredient IDs (allergens) to exclude. Max 50 IDs.",
        alias="excluirAlergenos",
    ),
    uow: UnitOfWork = Depends(get_uow),
    current_user: Optional[Usuario] = Depends(get_optional_user),
) -> list[ProductoResponse]:
    """List active products with pagination. incluir_eliminados=true requires STOCK/ADMIN."""
    # Parse excluirAlergenos query param — CSV string → list[int]
    alergeno_ids: List[int] = []
    if excluirAlergenos:
        try:
            alergeno_ids = [int(x.strip()) for x in excluirAlergenos.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "about:blank",
                    "title": "Unprocessable Entity",
                    "status": 422,
                    "detail": "excluirAlergenos must be a comma-separated list of integers (e.g. '1,3,7')",
                },
            )
        if len(alergeno_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "about:blank",
                    "title": "Unprocessable Entity",
                    "status": 422,
                    "detail": "excluirAlergenos supports at most 50 IDs per request",
                },
            )

    async with uow:
        return await service.list_productos(
            uow,
            skip=skip,
            limit=limit,
            incluir_eliminados=incluir_eliminados,
            current_user=current_user,
            excluir_alergenos=alergeno_ids,
        )


@router.get(
    "/{producto_id}/categorias",
    response_model=list[CategoriaCompacta],
    summary="List product categories",
    description=(
        "Return the list of categories associated with a product. "
        "No authentication required."
    ),
)
async def list_categorias_producto(
    producto_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[CategoriaCompacta]:
    """Return all categories for a Producto, or 404 if the product does not exist."""
    async with uow:
        return await service.list_categorias_producto(uow, producto_id)


@router.put(
    "/{producto_id}/categorias",
    response_model=list[CategoriaCompacta],
    status_code=status.HTTP_200_OK,
    summary="Replace product categories",
    description=(
        "Atomically replace all category associations for a product. "
        "An empty lista removes all associations. "
        "Requires STOCK or ADMIN role."
    ),
)
async def set_categorias_producto(
    producto_id: int,
    data: ProductoCategoriaSetRequest,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> list[CategoriaCompacta]:
    """Replace the full set of categories for a Producto atomically."""
    async with uow:
        return await service.set_categorias_producto(uow, producto_id, data)


@router.delete(
    "/{producto_id}/categorias/{categoria_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a product category",
    description=(
        "Remove a single category association from a product. "
        "Returns 404 if the association does not exist. "
        "Requires STOCK or ADMIN role."
    ),
)
async def remove_categoria_producto(
    producto_id: int,
    categoria_id: int,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Remove a single category association from a Producto."""
    async with uow:
        await service.remove_categoria_producto(uow, producto_id, categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{producto_id}/ingredientes",
    response_model=list[IngredienteCompacto],
    summary="List product ingredients",
    description=(
        "Return the list of ingredients associated with a product, "
        "including es_removible flag from the pivot table. "
        "No authentication required."
    ),
)
async def list_ingredientes_producto(
    producto_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[IngredienteCompacto]:
    """Return all ingredients for a Producto, or 404 if the product does not exist."""
    async with uow:
        return await service.list_ingredientes_producto(uow, producto_id)


@router.put(
    "/{producto_id}/ingredientes",
    response_model=list[IngredienteCompacto],
    status_code=status.HTTP_200_OK,
    summary="Replace product ingredients",
    description=(
        "Atomically replace all ingredient associations for a product. "
        "Each entry includes ingrediente_id and es_removible. "
        "An empty list removes all associations. "
        "Requires STOCK or ADMIN role."
    ),
)
async def set_ingredientes_producto(
    producto_id: int,
    data: ProductoIngredienteSetRequest,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> list[IngredienteCompacto]:
    """Replace the full set of ingredients for a Producto atomically."""
    async with uow:
        return await service.set_ingredientes_producto(uow, producto_id, data)


@router.delete(
    "/{producto_id}/ingredientes/{ingrediente_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a product ingredient",
    description=(
        "Remove a single ingredient association from a product. "
        "Returns 404 if the association does not exist. "
        "Requires STOCK or ADMIN role."
    ),
)
async def remove_ingrediente_producto(
    producto_id: int,
    ingrediente_id: int,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Remove a single ingredient association from a Producto."""
    async with uow:
        await service.remove_ingrediente_producto(uow, producto_id, ingrediente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Get product by ID",
    description="Return a single active product by its primary key. No authentication required.",
)
async def get_producto(
    producto_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoResponse:
    """Return a single Producto or 404."""
    async with uow:
        return await service.get_producto_by_id(uow, producto_id)


# ---------------------------------------------------------------------------
# Protected POST / PUT / DELETE / PATCH endpoints (STOCK or ADMIN)
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
    description="Create a new product. Requires STOCK or ADMIN role.",
)
async def create_producto(
    data: ProductoCreate,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoResponse:
    """Create and persist a new Producto."""
    async with uow:
        return await service.create_producto(uow, data)


@router.put(
    "/{producto_id}",
    response_model=ProductoResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a product",
    description=(
        "Partially update a product. Only provided fields are modified. "
        "Requires STOCK or ADMIN role."
    ),
)
async def update_producto(
    producto_id: int,
    data: ProductoUpdate,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoResponse:
    """Update an existing Producto — partial update."""
    async with uow:
        return await service.update_producto(uow, producto_id, data)


@router.delete(
    "/{producto_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a product",
    description=(
        "Soft-delete a product (sets eliminado_en). "
        "Requires STOCK or ADMIN role."
    ),
)
async def delete_producto(
    producto_id: int,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Soft-delete a Producto."""
    async with uow:
        await service.delete_producto(uow, producto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{producto_id}/stock",
    response_model=ProductoResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product stock",
    description=(
        "Update only the stock_cantidad field of a product. "
        "stock_cantidad must be >= 0. "
        "Requires STOCK or ADMIN role."
    ),
)
async def patch_stock(
    producto_id: int,
    data: ProductoStockUpdate,
    _: Usuario = Depends(require_role(["STOCK", "ADMIN"])),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoResponse:
    """Update stock_cantidad for a Producto."""
    async with uow:
        return await service.patch_stock(uow, producto_id, data)
