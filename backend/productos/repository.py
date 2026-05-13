"""
ProductoRepository — extends BaseRepository[Producto] with product-specific methods.

Adds:
- list_active(skip, limit, incluir_eliminados): filtered list ordered by nombre
- list_active_excluding_alergenos(skip, limit, alergeno_ids): allergen-filtered list

ProductoCategoriaRepository — manages the producto_categoria N:M pivot table.

Adds:
- get_categorias(producto_id): list associated Categoria rows
- set_categorias(producto_id, categoria_ids): atomic full-replacement
- get_association(producto_id, categoria_id): fetch a single pivot row
- remove_categoria(producto_id, categoria_id): delete a single pivot row

ProductoIngredienteRepository — manages the producto_ingrediente N:M pivot table.

Adds:
- get_ingredientes(producto_id): list (Ingrediente, es_removible) pairs
- set_ingredientes(producto_id, items): atomic full-replacement
- get_association(producto_id, ingrediente_id): fetch a single pivot row
- remove_ingrediente(producto_id, ingrediente_id): delete a single pivot row
"""

from sqlalchemy import delete, select

from core.models import Categoria, Ingrediente, Producto, ProductoCategoria, ProductoIngrediente
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

    async def list_active_excluding_alergenos(
        self,
        skip: int = 0,
        limit: int = 100,
        alergeno_ids: list[int] = [],
    ) -> list[Producto]:
        """
        Return paginated list of active products that do NOT contain ANY of the
        specified allergen ingredient IDs.

        Uses a NOT-IN subquery against producto_ingrediente for correctness.
        Returns all active products if alergeno_ids is empty.

        Args:
            skip: Pagination offset.
            limit: Maximum records to return (capped at 1000).
            alergeno_ids: List of ingrediente IDs to exclude. Products that have
                at least one of these ingredients are excluded from the result.

        Returns:
            List of Producto instances ordered by nombre.
        """
        stmt = (
            select(Producto)
            .where(Producto.eliminado_en.is_(None))
            .order_by(Producto.nombre)
        )

        if alergeno_ids:
            # Subquery: product IDs that contain at least one allergen ingredient
            subq = (
                select(ProductoIngrediente.producto_id)
                .where(ProductoIngrediente.ingrediente_id.in_(alergeno_ids))
                .distinct()
                .scalar_subquery()
            )
            stmt = stmt.where(Producto.id.notin_(subq))

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


class ProductoIngredienteRepository:
    """
    Repository for the producto_ingrediente N:M pivot table.

    Provides atomic set/remove/query operations for ingredient associations.
    Does NOT raise HTTPException — business-rule validation belongs in Service.
    """

    def __init__(self, session) -> None:
        self.session = session

    async def get_ingredientes(
        self, producto_id: int
    ) -> list[tuple[Ingrediente, bool]]:
        """
        Return (Ingrediente, es_removible) pairs for a product, ordered by nombre.

        Args:
            producto_id: Product primary key.

        Returns:
            List of (Ingrediente, es_removible) tuples ordered by Ingrediente.nombre.
        """
        stmt = (
            select(Ingrediente, ProductoIngrediente.es_removible)
            .join(
                ProductoIngrediente,
                ProductoIngrediente.ingrediente_id == Ingrediente.id,
            )
            .where(ProductoIngrediente.producto_id == producto_id)
            .where(Ingrediente.eliminado_en.is_(None))
            .order_by(Ingrediente.nombre)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def set_ingredientes(
        self,
        producto_id: int,
        items: list[dict],
    ) -> None:
        """
        Atomically replace all ingredient associations for a product.

        Deletes all existing rows in producto_ingrediente for the product,
        then inserts the new set. An empty list removes all associations.

        Args:
            producto_id: Product primary key.
            items: List of dicts with 'ingrediente_id' and 'es_removible' keys.
        """
        # DELETE all existing associations for this product
        stmt_del = delete(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == producto_id
        )
        await self.session.execute(stmt_del)
        await self.session.flush()

        # INSERT new associations
        for item in items:
            pivot = ProductoIngrediente(
                producto_id=producto_id,
                ingrediente_id=item["ingrediente_id"],
                es_removible=item.get("es_removible", False),
            )
            self.session.add(pivot)

        if items:
            await self.session.flush()

    async def get_association(
        self, producto_id: int, ingrediente_id: int
    ) -> ProductoIngrediente | None:
        """
        Return the pivot row for a specific product-ingredient pair, or None.

        Args:
            producto_id: Product primary key.
            ingrediente_id: Ingredient primary key.

        Returns:
            ProductoIngrediente instance if found, None otherwise.
        """
        stmt = select(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == producto_id,
            ProductoIngrediente.ingrediente_id == ingrediente_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_ingrediente(
        self, producto_id: int, ingrediente_id: int
    ) -> None:
        """
        Delete a single product-ingredient association.

        Args:
            producto_id: Product primary key.
            ingrediente_id: Ingredient primary key.
        """
        stmt = delete(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == producto_id,
            ProductoIngrediente.ingrediente_id == ingrediente_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()
