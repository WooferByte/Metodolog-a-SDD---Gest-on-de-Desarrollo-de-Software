"""Add preference_id to pagos and create pago_webhook_log table

Adds preference_id column to pagos table (needed for MP preference tracking)
and creates pago_webhook_log for webhook audit trail.

Revision ID: 010_pagos_webhook_log
Revises: 009_add_direcciones_entrega_usuario_index
Create Date: 2026-05-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "010_pagos_webhook_log"
down_revision = "009_add_direcciones_entrega_usuario_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add preference_id column to pagos table (idempotent)
    op.execute(
        "ALTER TABLE pagos ADD COLUMN IF NOT EXISTS preference_id VARCHAR(255)"
    )

    # Create pago_webhook_log table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pago_webhook_log (
            id SERIAL PRIMARY KEY,
            mercadopago_id VARCHAR(255),
            topic VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL,
            procesado BOOLEAN NOT NULL DEFAULT FALSE,
            error_msg TEXT,
            creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        )
        """
    )

    # Indexes for pago_webhook_log
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_webhook_log_mp_id ON pago_webhook_log(mercadopago_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_webhook_log_created ON pago_webhook_log(creado_en)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_webhook_log_created")
    op.execute("DROP INDEX IF EXISTS idx_webhook_log_mp_id")
    op.execute("DROP TABLE IF EXISTS pago_webhook_log")
    op.execute("ALTER TABLE pagos DROP COLUMN IF EXISTS preference_id")
