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
    op.execute(
        """
        ALTER TABLE detalle_pedido
          ALTER COLUMN ingredientes_excluidos TYPE INTEGER[]
          USING CASE
            WHEN ingredientes_excluidos IS NULL THEN NULL
            WHEN ingredientes_excluidos = '' THEN '{}'::INTEGER[]
            ELSE (
              SELECT array_agg(x::integer)
              FROM json_array_elements_text(ingredientes_excluidos::json) AS t(x)
            )
          END
    """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE detalle_pedido
          ALTER COLUMN ingredientes_excluidos TYPE VARCHAR
          USING CASE
            WHEN ingredientes_excluidos IS NULL THEN NULL
            ELSE array_to_json(ingredientes_excluidos)::text
          END
    """
    )
