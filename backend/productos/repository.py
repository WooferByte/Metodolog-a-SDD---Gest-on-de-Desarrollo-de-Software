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

from typing import Optional

from sqlalchemy import delete, func, or_, select

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

    def _build_base_stmt(
        self,
        incluir_eliminados: bool = False,
        q: Optional[str] = None,
        categoria_id: Optional[int] = None,
        alergeno_ids: list[int] = [],
    ):
        """
        Build the shared base SELECT statement with all active filters applied.

        Called by both list_active and count_active to guarantee identical WHERE
        clauses (DRY — avoids count/list divergence bugs).

        Applies:
        - eliminado_en IS NULL (always)
        - disponible = true when not incluir_eliminados (D-05: RN-CA08 correctness fix)
        - ILIKE on nombre OR descripcion if q is non-empty (D-01)
        - JOIN on ProductoCategoria + DISTINCT if categoria_id is given (D-02)
        - NOT IN subquery for alergeno exclusion if alergeno_ids is non-empty

        Args:
            incluir_eliminados: Include soft-deleted products (caller enforces role).
            q: Optional ILIKE search string for nombre/descripcion.
            categoria_id: Optional category ID filter via pivot JOIN.
            alergeno_ids: Allergen ingredient IDs to exclude (NOT IN subquery).

        Returns:
            SQLAlchemy Select statement (no OFFSET/LIMIT applied).
        """
        stmt = select(Producto).order_by(Producto.nombre)

        if not incluir_eliminados:
            stmt = stmt.where(Producto.eliminado_en.is_(None))
            # D-05: public list filters disponible=true per RN-CA08
            stmt = stmt.where(Producto.disponible.is_(True))

        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Producto.nombre.ilike(pattern),
                    Producto.descripcion.ilike(pattern),
                )
            )

        if categoria_id is not None:
            # D-02: JOIN on pivot table + DISTINCT to avoid duplicate rows
            stmt = (
                stmt
                .join(ProductoCategoria, ProductoCategoria.producto_id == Producto.id)
                .where(ProductoCategoria.categoria_id == categoria_id)
                .distinct()
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

        return stmt

    async def list_active(
        self,
        skip: int = 0,
        limit: int = 100,
        incluir_eliminados: bool = False,
        q: Optional[str] = None,
        categoria_id: Optional[int] = None,
        alergeno_ids: list[int] = [],
    ) -> list[Producto]:
        """
        Return paginated list of products with all optional filters applied.

        Unified method replacing the former list_active + list_active_excluding_alergenos
        (D-04). Supports text search (q), category filter (categoria_id), allergen
        exclusion (alergeno_ids), and soft-delete inclusion (incluir_eliminados).

        Args:
            skip: Pagination offset.
            limit: Maximum records to return (capped at 1000).
            incluir_eliminados: If False (default), only return products with
                eliminado_en IS NULL and disponible = true (RN-CA08).
            q: Optional ILIKE search string for nombre/descripcion.
            categoria_id: Optional category ID filter.
            alergeno_ids: List of ingrediente IDs to exclude.

        Returns:
            List of Producto instances ordered by nombre.
        """
        stmt = self._build_base_stmt(
            incluir_eliminados=incluir_eliminados,
            q=q,
            categoria_id=categoria_id,
            alergeno_ids=alergeno_ids,
        )
        stmt = stmt.offset(skip).limit(min(limit, 1000))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_locked(self, producto_id: int) -> Optional[Producto]:
        """
        Fetch a single active product with a SELECT ... FOR UPDATE lock.

        Prevents race conditions when multiple concurrent orders try to decrement
        stock for the same product (RN-PE04).

        Filters: eliminado_en IS NULL AND disponible = True.
        A product that is soft-deleted or marked unavailable returns None,
        letting the caller raise HTTP 422 "producto inválido".

        Args:
            producto_id: Primary key of the product to lock.

        Returns:
            Producto instance (locked) if active and available, None otherwise.
        """
        stmt = (
            select(Producto)
            .where(
                Producto.id == producto_id,
                Producto.eliminado_en.is_(None),
                Producto.disponible.is_(True),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_ids(self, producto_ids: list[int]) -> list[Producto]:
        """
        Batch-fetch products by primary key list (single IN query).

        Returns all rows matching the given IDs without applying any
        disponible/eliminado_en filters — callers need the raw records to
        classify products as invalid (soft-deleted, unavailable, or missing).

        Used by the checkout pre-validation service to detect stock shortfalls,
        price drift, and unavailable/deleted products in O(1) DB round-trips.

        Args:
            producto_ids: List of product primary keys to fetch.

        Returns:
            List of Producto instances (may include soft-deleted / unavailable).
            Preserves database order (no guaranteed sort).
        """
        if not producto_ids:
            return []
        stmt = select(Producto).where(Producto.id.in_(producto_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_active(
        self,
        incluir_eliminados: bool = False,
        q: Optional[str] = None,
        categoria_id: Optional[int] = None,
        alergeno_ids: list[int] = [],
    ) -> int:
        """
        Return the total count of products matching the given filters.

        Uses the same WHERE clauses as list_active (via _build_base_stmt) without
        OFFSET/LIMIT, wrapped in SELECT COUNT(DISTINCT p.id) for correctness when
        JOIN + DISTINCT is involved.

        Args:
            incluir_eliminados: Include soft-deleted products.
            q: Optional ILIKE search string.
            categoria_id: Optional category ID filter.
            alergeno_ids: Allergen ingredient IDs to exclude.

        Returns:
            Integer count of matching products.
        """
        base = self._build_base_stmt(
            incluir_eliminados=incluir_eliminados,
            q=q,
            categoria_id=categoria_id,
            alergeno_ids=alergeno_ids,
        )
        # Wrap as subquery and count — ensures DISTINCT is respected
        subq = base.subquery()
        count_stmt = select(func.count()).select_from(subq)
        result = await self.session.execute(count_stmt)
        return result.scalar_one()


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
