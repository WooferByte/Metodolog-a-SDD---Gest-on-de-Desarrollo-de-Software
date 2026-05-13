"""
CategoriaRepository — extends BaseRepository[Categoria] with tree-specific methods.

Adds:
- get_tree(root_id): PostgreSQL recursive CTE for full/subtree traversal
- has_active_products(categoria_id): check before allowing soft-delete
"""

from typing import Optional

from sqlalchemy import text

from core.models import Categoria
from infrastructure.repositories.base_repository import BaseRepository


class CategoriaRepository(BaseRepository[Categoria]):
    """
    Categoria-specific repository.

    Inherits all generic CRUD operations from BaseRepository[Categoria].
    Adds recursive CTE tree traversal and product-guard check.
    """

    def __init__(self, session) -> None:
        super().__init__(session, Categoria)

    async def get_tree(self, root_id: Optional[int] = None) -> list[dict]:
        """
        Return the full category tree (or a subtree) as a flat list with depth.

        Uses a PostgreSQL recursive CTE over the adjacency-list padre_id column.
        Filtered to exclude soft-deleted rows (eliminado_en IS NULL).

        Args:
            root_id: If None, return the entire forest (all root categories and
                     their descendants).  If set, return the category identified
                     by root_id PLUS all its descendants.

        Returns:
            List of dicts with keys:
              id, nombre, descripcion, padre_id, creado_en, actualizado_en, depth
            Ordered by depth ASC, then nombre ASC.
        """
        if root_id is None:
            sql = text(
                """
                WITH RECURSIVE arbol AS (
                    SELECT
                        id, nombre, descripcion, padre_id,
                        creado_en, actualizado_en,
                        0 AS depth
                    FROM categorias
                    WHERE eliminado_en IS NULL
                      AND padre_id IS NULL
                    UNION ALL
                    SELECT
                        c.id, c.nombre, c.descripcion, c.padre_id,
                        c.creado_en, c.actualizado_en,
                        a.depth + 1
                    FROM categorias c
                    JOIN arbol a ON c.padre_id = a.id
                    WHERE c.eliminado_en IS NULL
                )
                SELECT * FROM arbol ORDER BY depth, nombre
                """
            )
            result = await self.session.execute(sql)
        else:
            sql = text(
                """
                WITH RECURSIVE arbol AS (
                    SELECT
                        id, nombre, descripcion, padre_id,
                        creado_en, actualizado_en,
                        0 AS depth
                    FROM categorias
                    WHERE eliminado_en IS NULL
                      AND id = :root_id
                    UNION ALL
                    SELECT
                        c.id, c.nombre, c.descripcion, c.padre_id,
                        c.creado_en, c.actualizado_en,
                        a.depth + 1
                    FROM categorias c
                    JOIN arbol a ON c.padre_id = a.id
                    WHERE c.eliminado_en IS NULL
                )
                SELECT * FROM arbol ORDER BY depth, nombre
                """
            )
            result = await self.session.execute(sql, {"root_id": root_id})

        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def has_active_products(self, categoria_id: int) -> bool:
        """
        Return True if the category has at least one active (non-deleted) product.

        Uses a quick EXISTS-style query with LIMIT 1.

        Args:
            categoria_id: ID of the category to check.

        Returns:
            True if there is at least one Producto with eliminado_en IS NULL
            linked to this category via producto_categoria.
        """
        sql = text(
            """
            SELECT 1
            FROM producto_categoria pc
            JOIN productos p ON pc.producto_id = p.id
            WHERE pc.categoria_id = :cid
              AND p.eliminado_en IS NULL
            LIMIT 1
            """
        )
        result = await self.session.execute(sql, {"cid": categoria_id})
        return result.first() is not None
