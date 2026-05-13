"""Add partial index on categorias.padre_id for CTE recursive join performance

Adds idx_categorias_padre_id (partial: WHERE eliminado_en IS NULL) to accelerate
the recursive CTE join used by the GET /api/v1/categorias/tree endpoint.

Revision ID: 006_add_categoria_padre_id_index
Revises: 005_ingredientes_excluidos_integer_array
Create Date: 2026-05-12 00:00:00.000000
"""
from alembic import op

revision = "006_add_categoria_padre_id_index"
down_revision = "005_ingredientes_excluidos_integer_array"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE INDEX IF NOT EXISTS (without CONCURRENTLY so it runs inside alembic transaction)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_categorias_padre_id
        ON categorias (padre_id)
        WHERE eliminado_en IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_categorias_padre_id")
