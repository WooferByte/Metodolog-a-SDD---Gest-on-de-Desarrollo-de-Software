"""Convert ingredientes_excluidos from VARCHAR to INTEGER[] in detalle_pedido

INC-04: align column type with spec (RN-PE07 — personalización como array nativo PostgreSQL).

Revision ID: 005_ingredientes_excluidos_integer_array
Revises: 004_rename_es_principal_to_es_predeterminada
Create Date: 2026-05-11 00:01:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_ingredientes_excluidos_integer_array"
down_revision = "004_rename_es_principal_to_es_predeterminada"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL doesn't support subqueries in ALTER COLUMN USING.
    # Use add-column + UPDATE (subqueries allowed) + drop + rename instead.
    op.execute("ALTER TABLE detalle_pedido ADD COLUMN ingredientes_excluidos_new INTEGER[]")
    op.execute(
        """
        UPDATE detalle_pedido
        SET ingredientes_excluidos_new = (
          SELECT array_agg(x::integer)
          FROM json_array_elements_text(ingredientes_excluidos::json) AS t(x)
        )
        WHERE ingredientes_excluidos IS NOT NULL AND ingredientes_excluidos <> ''
        """
    )
    op.execute("ALTER TABLE detalle_pedido DROP COLUMN ingredientes_excluidos")
    op.execute("ALTER TABLE detalle_pedido RENAME COLUMN ingredientes_excluidos_new TO ingredientes_excluidos")


def downgrade() -> None:
    op.execute("ALTER TABLE detalle_pedido ADD COLUMN ingredientes_excluidos_old VARCHAR")
    op.execute(
        """
        UPDATE detalle_pedido
        SET ingredientes_excluidos_old = array_to_json(ingredientes_excluidos)::text
        WHERE ingredientes_excluidos IS NOT NULL
        """
    )
    op.execute("ALTER TABLE detalle_pedido DROP COLUMN ingredientes_excluidos")
    op.execute("ALTER TABLE detalle_pedido RENAME COLUMN ingredientes_excluidos_old TO ingredientes_excluidos")
