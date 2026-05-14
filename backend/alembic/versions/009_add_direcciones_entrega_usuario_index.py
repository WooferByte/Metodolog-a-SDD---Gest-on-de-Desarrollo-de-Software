"""Add partial index on direcciones_entrega(usuario_id) for active records

Accelerates list_by_usuario and count_active_by_usuario queries that filter
by usuario_id WHERE eliminado_en IS NULL (the hot path for address CRUD).

Revision ID: 009_add_direcciones_entrega_usuario_index
Revises: 008_add_productos_index
Create Date: 2026-05-14 00:00:00.000000
"""
from alembic import op

revision = "009_add_direcciones_entrega_usuario_index"
down_revision = "008_add_productos_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_direcciones_entrega_usuario
        ON direcciones_entrega (usuario_id)
        WHERE eliminado_en IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_direcciones_entrega_usuario")
