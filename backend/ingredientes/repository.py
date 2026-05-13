"""
IngredienteRepository — extends BaseRepository[Ingrediente] with allergen-specific methods.

Adds:
- has_active_products(ingrediente_id): check before allowing soft-delete
- list_by_alergeno(es_alergeno, skip, limit): filtered list ordered by nombre
"""

from sqlalchemy import select, text

from core.models import Ingrediente
from infrastructure.repositories.base_repository import BaseRepository


class IngredienteRepository(BaseRepository[Ingrediente]):
    """
    Ingrediente-specific repository.

    Inherits all generic CRUD operations from BaseRepository[Ingrediente].
    Adds allergen-filtered list and active-products guard check.
    """

    def __init__(self, session) -> None:
        super().__init__(session, Ingrediente)

    async def has_active_products(self, ingrediente_id: int) -> bool:
        """
        Return True if the ingredient is used by at least one active (non-deleted) product.

        Uses a quick EXISTS-style query with LIMIT 1 joining producto_ingrediente
        to productos filtering productos.eliminado_en IS NULL.

        Args:
            ingrediente_id: ID of the ingredient to check.

        Returns:
            True if there is at least one Producto with eliminado_en IS NULL
            linked to this ingredient via producto_ingrediente.
        """
        sql = text(
            """
            SELECT 1
            FROM producto_ingrediente pi
            JOIN productos p ON pi.producto_id = p.id
            WHERE pi.ingrediente_id = :iid
              AND p.eliminado_en IS NULL
            LIMIT 1
            """
        )
        result = await self.session.execute(sql, {"iid": ingrediente_id})
        return result.first() is not None

    async def list_by_alergeno(
        self, es_alergeno: bool, skip: int = 0, limit: int = 100
    ) -> list[Ingrediente]:
        """Return paginated active ingredients filtered by es_alergeno, ordered by nombre."""
        stmt = (
            select(Ingrediente)
            .where(Ingrediente.eliminado_en == None)  # noqa: E711
            .where(Ingrediente.es_alergeno == es_alergeno)
            .order_by(Ingrediente.nombre)
            .offset(skip)
            .limit(min(limit, 1000))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
