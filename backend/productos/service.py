"""
Product service — business logic layer for productos module.

Architecture: Router → Service → UoW → Repository → Model
- This module is the ONLY layer that raises HTTPException.
- Never calls session.commit() directly (handled by UoW).
- Validates business rules: existence checks, role guards for incluir_eliminados.
"""

from typing import Optional

from fastapi import HTTPException, status

from core.models import Categoria, Ingrediente, Producto, Usuario
from infrastructure.uow import UnitOfWork
import math

from productos.schemas import (
    CategoriaCompacta,
    IngredienteCompacto,
    PaginatedProductosResponse,
    ProductoCategoriaSetRequest,
    ProductoCreate,
    ProductoIngredienteSetRequest,
    ProductoResponse,
    ProductoStockUpdate,
    ProductoUpdate,
)


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
    excluir_alergenos: list[int] = [],
    q: Optional[str] = None,
    categoria_id: Optional[int] = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedProductosResponse:
    """
    Return a paginated envelope of products ordered by nombre.

    If incluir_eliminados=True, enforces that the caller has STOCK or ADMIN role.
    Supports text search (q), category filter (categoria_id), and allergen exclusion.
    Returns PaginatedProductosResponse { items, total, page, size, pages }.

    Args:
        uow: Unit of Work.
        skip: Raw offset (legacy — use page/size for canonical pagination).
        limit: Raw limit (legacy — use page/size for canonical pagination).
        incluir_eliminados: If True, include soft-deleted products (RN-CA10 — requires STOCK or ADMIN).
        current_user: Authenticated user (may be None for public requests).
        excluir_alergenos: List of ingrediente IDs to exclude (allergen filter).
        q: Optional ILIKE search string for nombre/descripcion.
        categoria_id: Optional category ID filter.
        page: 1-based page number (used to derive skip when provided via router).
        size: Page size (used as limit when provided via router).

    Returns:
        PaginatedProductosResponse with items, total, page, size, pages.

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

    productos = await uow.productos.list_active(
        skip=skip,
        limit=limit,
        incluir_eliminados=incluir_eliminados,
        q=q,
        categoria_id=categoria_id,
        alergeno_ids=excluir_alergenos,
    )

    total = await uow.productos.count_active(
        incluir_eliminados=incluir_eliminados,
        q=q,
        categoria_id=categoria_id,
        alergeno_ids=excluir_alergenos,
    )

    pages = math.ceil(total / size) if size > 0 else 0

    return PaginatedProductosResponse(
        items=productos,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def _categorias_to_compacta(categorias: list[Categoria]) -> list[CategoriaCompacta]:
    """Map a list of Categoria ORM instances to CategoriaCompacta schemas."""
    return [
        CategoriaCompacta(id=c.id, nombre=c.nombre, padre_id=c.padre_id)
        for c in categorias
    ]


def _ingredientes_to_compacto(
    pairs: list[tuple[Ingrediente, bool]],
) -> list[IngredienteCompacto]:
    """
    Map a list of (Ingrediente, es_removible) pairs to IngredienteCompacto schemas.

    es_removible comes from the pivot table, not from the Ingrediente entity.
    """
    return [
        IngredienteCompacto(
            id=ing.id,
            nombre=ing.nombre,
            es_alergeno=ing.es_alergeno,
            es_removible=es_removible,
        )
        for ing, es_removible in pairs
    ]


async def get_producto_by_id(
    uow: UnitOfWork,
    producto_id: int,
) -> ProductoResponse:
    """
    Return a single Producto by primary key, enriched with its categories and ingredients.

    Args:
        uow: Unit of Work.
        producto_id: Product ID to retrieve.

    Returns:
        ProductoResponse with categorias and ingredientes lists populated.

    Raises:
        HTTPException 404 if not found or soft-deleted.
    """
    producto = await _get_or_404(uow, producto_id)
    categorias = await uow.producto_categorias.get_categorias(producto_id)
    ingrediente_pairs = await uow.producto_ingredientes.get_ingredientes(producto_id)
    return ProductoResponse(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio_base=producto.precio_base,
        stock_cantidad=producto.stock_cantidad,
        disponible=producto.disponible,
        imagen_url=producto.imagen_url,
        creado_en=producto.creado_en,
        categorias=_categorias_to_compacta(categorias),
        ingredientes=_ingredientes_to_compacto(ingrediente_pairs),
    )


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


async def list_categorias_producto(
    uow: UnitOfWork,
    producto_id: int,
) -> list[CategoriaCompacta]:
    """
    Return the list of categories associated with a product.

    Args:
        uow: Unit of Work.
        producto_id: Product ID to look up.

    Returns:
        List of CategoriaCompacta schemas (may be empty).

    Raises:
        HTTPException 404 if the product does not exist or is soft-deleted.
    """
    await _get_or_404(uow, producto_id)
    categorias = await uow.producto_categorias.get_categorias(producto_id)
    return _categorias_to_compacta(categorias)


async def set_categorias_producto(
    uow: UnitOfWork,
    producto_id: int,
    data: ProductoCategoriaSetRequest,
) -> list[CategoriaCompacta]:
    """
    Atomically replace all category associations for a product.

    Validates each categoria_id exists and is not soft-deleted before writing.

    Args:
        uow: Unit of Work.
        producto_id: Product ID to update.
        data: ProductoCategoriaSetRequest with the new set of categoria_ids.

    Returns:
        Updated list of CategoriaCompacta schemas.

    Raises:
        HTTPException 404 if the product or any category does not exist.
    """
    await _get_or_404(uow, producto_id)

    # Validate each category exists (D-03: Service owns this check)
    for cat_id in data.categoria_ids:
        categoria = await uow.categorias.get_by_id(cat_id)
        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "about:blank",
                    "title": "Not Found",
                    "status": 404,
                    "detail": f"Categoria {cat_id} not found or has been deleted",
                },
            )

    await uow.producto_categorias.set_categorias(producto_id, data.categoria_ids)
    categorias = await uow.producto_categorias.get_categorias(producto_id)
    return _categorias_to_compacta(categorias)


async def remove_categoria_producto(
    uow: UnitOfWork,
    producto_id: int,
    categoria_id: int,
) -> None:
    """
    Remove a single category association from a product.

    Args:
        uow: Unit of Work.
        producto_id: Product ID.
        categoria_id: Category ID to disassociate.

    Raises:
        HTTPException 404 if the product does not exist or the association is absent.
    """
    await _get_or_404(uow, producto_id)

    association = await uow.producto_categorias.get_association(
        producto_id, categoria_id
    )
    if association is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": (
                    f"Association between producto {producto_id} "
                    f"and categoria {categoria_id} not found"
                ),
            },
        )

    await uow.producto_categorias.remove_categoria(producto_id, categoria_id)


async def list_ingredientes_producto(
    uow: UnitOfWork,
    producto_id: int,
) -> list[IngredienteCompacto]:
    """
    Return the list of ingredients associated with a product.

    Args:
        uow: Unit of Work.
        producto_id: Product ID to look up.

    Returns:
        List of IngredienteCompacto schemas (may be empty).

    Raises:
        HTTPException 404 if the product does not exist or is soft-deleted.
    """
    await _get_or_404(uow, producto_id)
    pairs = await uow.producto_ingredientes.get_ingredientes(producto_id)
    return _ingredientes_to_compacto(pairs)


async def set_ingredientes_producto(
    uow: UnitOfWork,
    producto_id: int,
    data: ProductoIngredienteSetRequest,
) -> list[IngredienteCompacto]:
    """
    Atomically replace all ingredient associations for a product.

    Validates each ingrediente_id exists and is not soft-deleted before writing.

    Args:
        uow: Unit of Work.
        producto_id: Product ID to update.
        data: ProductoIngredienteSetRequest with the new set of ingredient associations.

    Returns:
        Updated list of IngredienteCompacto schemas.

    Raises:
        HTTPException 404 if the product or any ingredient does not exist.
    """
    await _get_or_404(uow, producto_id)

    # Validate each ingredient exists and is not soft-deleted
    for item in data.ingredientes:
        ingrediente = await uow.ingredientes.get_by_id(item.ingrediente_id)
        if ingrediente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "about:blank",
                    "title": "Not Found",
                    "status": 404,
                    "detail": f"Ingrediente {item.ingrediente_id} not found or has been deleted",
                },
            )

    items = [
        {"ingrediente_id": item.ingrediente_id, "es_removible": item.es_removible}
        for item in data.ingredientes
    ]
    await uow.producto_ingredientes.set_ingredientes(producto_id, items)
    pairs = await uow.producto_ingredientes.get_ingredientes(producto_id)
    return _ingredientes_to_compacto(pairs)


async def remove_ingrediente_producto(
    uow: UnitOfWork,
    producto_id: int,
    ingrediente_id: int,
) -> None:
    """
    Remove a single ingredient association from a product.

    Args:
        uow: Unit of Work.
        producto_id: Product ID.
        ingrediente_id: Ingredient ID to disassociate.

    Raises:
        HTTPException 404 if the product does not exist or the association is absent.
    """
    await _get_or_404(uow, producto_id)

    association = await uow.producto_ingredientes.get_association(
        producto_id, ingrediente_id
    )
    if association is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": (
                    f"Association between producto {producto_id} "
                    f"and ingrediente {ingrediente_id} not found"
                ),
            },
        )

    if not association.es_removible:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "about:blank",
                "title": "Conflict",
                "status": 409,
                "detail": (
                    f"Ingrediente {ingrediente_id} no es removible del producto {producto_id}"
                ),
            },
        )

    await uow.producto_ingredientes.remove_ingrediente(producto_id, ingrediente_id)


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
