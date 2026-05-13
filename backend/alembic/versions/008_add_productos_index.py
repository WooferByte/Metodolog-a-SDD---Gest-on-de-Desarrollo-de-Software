"""Add partial index on productos.nombre for active-record lookup performance

Adds idx_productos_nombre_active (partial: WHERE eliminado_en IS NULL) to accelerate
lookup queries on active product names, consistent with the pattern established
by migrations 006 (categorias) and 007 (ingredientes).

Revision ID: 008_add_productos_index
Revises: 007_add_ingredientes_index
Create Date: 2026-05-13 00:00:00.000000
"""
from alembic import op

revision = "008_add_productos_index"
down_revision = "007_add_ingredientes_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE INDEX IF NOT EXISTS (without CONCURRENTLY so it runs inside alembic transaction)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_productos_nombre_active
        ON productos (nombre)
        WHERE eliminado_en IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_productos_nombre_active")
