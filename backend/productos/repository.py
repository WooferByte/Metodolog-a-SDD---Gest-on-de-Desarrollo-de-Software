"""
ProductoRepository — extends BaseRepository[Producto] with product-specific methods.

Adds:
- list_active(skip, limit, incluir_eliminados): filtered list ordered by nombre
"""

from sqlalchemy import select

from core.models import Producto
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
