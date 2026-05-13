"""Add partial index on ingredientes.nombre for active-record lookup performance

Adds idx_ingredientes_nombre_active (partial: WHERE eliminado_en IS NULL) to accelerate
lookup queries on active ingredient names, consistent with the pattern established
by migration 006 for categorias.

Revision ID: 007_add_ingredientes_index
Revises: 006_add_categoria_padre_id_index
Create Date: 2026-05-12 00:00:00.000000
"""
from alembic import op

revision = "007_add_ingredientes_index"
down_revision = "006_add_categoria_padre_id_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE INDEX IF NOT EXISTS (without CONCURRENTLY so it runs inside alembic transaction)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingredientes_nombre_active
        ON ingredientes (nombre)
        WHERE eliminado_en IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ingredientes_nombre_active")
