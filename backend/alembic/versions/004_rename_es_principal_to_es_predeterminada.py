"""Rename es_principal to es_predeterminada in direcciones_entrega

INC-02: align column name with spec (RN-DE02).

Revision ID: 004_rename_es_principal_to_es_predeterminada
Revises: 003_add_missing_fields
Create Date: 2026-05-11 00:00:00.000000
"""
from alembic import op

revision = "004_rename_es_principal_to_es_predeterminada"
down_revision = "003_add_missing_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "direcciones_entrega",
        "es_principal",
        new_column_name="es_predeterminada",
    )


def downgrade() -> None:
    op.alter_column(
        "direcciones_entrega",
        "es_predeterminada",
        new_column_name="es_principal",
    )
