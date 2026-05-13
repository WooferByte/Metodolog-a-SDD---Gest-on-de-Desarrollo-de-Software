"""
ProductoRepository — extends BaseRepository[Producto] with product-specific methods.

Adds:
- list_active(skip, limit, incluir_eliminados): filtered list ordered by nombre

ProductoCategoriaRepository — manages the producto_categoria N:M pivot table.

Adds:
- get_categorias(producto_id): list associated Categoria rows
- set_categorias(producto_id, categoria_ids): atomic full-replacement
- get_association(producto_id, categoria_id): fetch a single pivot row
- remove_categoria(producto_id, categoria_id): delete a single pivot row
"""

from sqlalchemy import delete, select

from core.models import Categoria, Producto, ProductoCategoria
from infrastructure.repositories.base_repository import BaseRepository


class ProductoRepository(BaseRepository[Producto]):
    """
    Producto-specific repository.

    Inherits all generic CRUD operations from BaseRepository[Producto].
    Adds active-filtered list with optional soft-deleted inclusion (RN-CA10).
    """

    def __init__(self, session) -> None:
        super().__init__(session, Producto)

    async def list_active(
        self,
        skip: int = 0,
        limit: int = 100,
        incluir_eliminados: bool = False,
    ) -> list[Producto]:
        """
        Return paginated list of products ordered by nombre.

        Uses ORM select (NOT raw SQL) to correctly reconstruct SQLModel objects.

        Args:
            skip: Pagination offset.
            limit: Maximum records to return (capped at 1000).
            incluir_eliminados: If False (default), only return products with
                eliminado_en IS NULL. If True, return all products including
                soft-deleted ones (caller must enforce role check before passing True).

        Returns:
            List of Producto instances ordered by nombre.
        """
        stmt = select(Producto).order_by(Producto.nombre)

        if not incluir_eliminados:
            stmt = stmt.where(Producto.eliminado_en.is_(None))

        stmt = stmt.offset(skip).limit(min(limit, 1000))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ProductoCategoriaRepository:
    """
    Repository for the producto_categoria N:M pivot table.

    Provides atomic set/remove/query operations for category associations.
    Does NOT raise HTTPException — business-rule validation belongs in Service.
    """

    def __init__(self, session) -> None:
        self.session = session

    async def get_categorias(self, producto_id: int) -> list[Categoria]:
        """
        Return all active (non-soft-deleted) Categoria rows for a product.

        Args:
            producto_id: Product primary key.

        Returns:
            List of Categoria instances ordered by nombre.
        """
        stmt = (
            select(Categoria)
            .join(ProductoCategoria, ProductoCategoria.categoria_id == Categoria.id)
            .where(ProductoCategoria.producto_id == producto_id)
            .where(Categoria.eliminado_en.is_(None))
            .order_by(Categoria.nombre)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def set_categorias(
        self, producto_id: int, categoria_ids: list[int]
    ) -> None:
        """
        Atomically replace all category associations for a product.

        Deletes all existing rows in producto_categoria for the product,
        then inserts the new set. An empty list removes all associations.

        Args:
            producto_id: Product primary key.
            categoria_ids: New set of category IDs to associate.
        """
        # DELETE all existing associations for this product
        stmt_del = delete(ProductoCategoria).where(
            ProductoCategoria.producto_id == producto_id
        )
        await self.session.execute(stmt_del)
        await self.session.flush()

        # INSERT new associations
        for cat_id in categoria_ids:
            pivot = ProductoCategoria(producto_id=producto_id, categoria_id=cat_id)
            self.session.add(pivot)

        if categoria_ids:
            await self.session.flush()

    async def get_association(
        self, producto_id: int, categoria_id: int
    ) -> ProductoCategoria | None:
        """
        Return the pivot row for a specific product-category pair, or None.

        Args:
            producto_id: Product primary key.
            categoria_id: Category primary key.

        Returns:
            ProductoCategoria instance if found, None otherwise.
        """
        stmt = select(ProductoCategoria).where(
            ProductoCategoria.producto_id == producto_id,
            ProductoCategoria.categoria_id == categoria_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_categoria(self, producto_id: int, categoria_id: int) -> None:
        """
        Delete a single product-category association.

        Args:
            producto_id: Product primary key.
            categoria_id: Category primary key.
        """
        stmt = delete(ProductoCategoria).where(
            ProductoCategoria.producto_id == producto_id,
            ProductoCategoria.categoria_id == categoria_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()
