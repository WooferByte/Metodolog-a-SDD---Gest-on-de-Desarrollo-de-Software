"""Add usuario_rol N:M table and migrate from rol_id

Revision ID: 002_add_usuario_rol_table
Revises: 001_initial_schema
Create Date: 2026-05-08 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_usuario_rol_table'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create usuario_rol pivot table
    op.create_table(
        'usuario_rol',
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_usuario_rol_usuario_id_usuarios', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], name='fk_usuario_rol_rol_id_roles', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('usuario_id', 'rol_id', name='pk_usuario_rol'),
    )

    # 2. Migrate existing data: copy rol_id → usuario_rol
    op.execute("""
        INSERT INTO usuario_rol (usuario_id, rol_id)
        SELECT id, rol_id FROM usuarios WHERE rol_id IS NOT NULL
    """)

    # 3. Drop FK constraint then column rol_id from usuarios
    op.drop_constraint('fk_usuarios_rol_id_roles', 'usuarios', type_='foreignkey')
    op.drop_column('usuarios', 'rol_id')


def downgrade() -> None:
    # Re-add rol_id column (take first role if multiple)
    op.add_column('usuarios', sa.Column('rol_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_usuarios_rol_id_roles', 'usuarios', 'roles', ['rol_id'], ['id']
    )
    op.execute("""
        UPDATE usuarios u
        SET rol_id = (
            SELECT rol_id FROM usuario_rol ur
            WHERE ur.usuario_id = u.id
            LIMIT 1
        )
    """)
    op.drop_table('usuario_rol')
