"""Add missing fields: direccion_snapshot, telefono, ultimo_login

Revision ID: 003_add_missing_fields
Revises: 002_add_usuario_rol_table
Create Date: 2026-05-08 11:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_missing_fields'
down_revision = '002_add_usuario_rol_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add direccion_snapshot to pedidos (snapshot of address at order time)
    op.add_column('pedidos', sa.Column('direccion_snapshot', sa.String(), nullable=True))

    # Add telefono and ultimo_login to usuarios
    op.add_column('usuarios', sa.Column('telefono', sa.String(length=20), nullable=True))
    op.add_column('usuarios', sa.Column('ultimo_login', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'ultimo_login')
    op.drop_column('usuarios', 'telefono')
    op.drop_column('pedidos', 'direccion_snapshot')
