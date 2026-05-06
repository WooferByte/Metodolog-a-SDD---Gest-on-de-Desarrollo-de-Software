"""Initial schema creation with 15 tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-05-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.String(length=500), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_roles'),
        sa.UniqueConstraint('nombre', name='uq_roles_nombre'),
    )
    op.create_index('ix_roles_nombre', 'roles', ['nombre'], unique=True)

    # Create estados_pedido table
    op.create_table(
        'estados_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.String(length=500), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_estados_pedido'),
        sa.UniqueConstraint('nombre', name='uq_estados_pedido_nombre'),
    )
    op.create_index('ix_estados_pedido_nombre', 'estados_pedido', ['nombre'], unique=True)

    # Create formas_pago table
    op.create_table(
        'formas_pago',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.String(length=500), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_formas_pago'),
        sa.UniqueConstraint('nombre', name='uq_formas_pago_nombre'),
    )
    op.create_index('ix_formas_pago_nombre', 'formas_pago', ['nombre'], unique=True)

    # Create usuarios table
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=True),
        sa.Column('rol_id', sa.Integer(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], name='fk_usuarios_rol_id_roles'),
        sa.PrimaryKeyConstraint('id', name='pk_usuarios'),
        sa.UniqueConstraint('email', name='uq_usuarios_email'),
    )
    op.create_index('ix_usuarios_email', 'usuarios', ['email'], unique=True)
    op.create_index('ix_usuarios_eliminado_en', 'usuarios', ['eliminado_en'])

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_refresh_tokens_usuario_id_usuarios', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_refresh_tokens'),
        sa.UniqueConstraint('token', name='uq_refresh_tokens_token'),
    )
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)

    # Create direcciones_entrega table
    op.create_table(
        'direcciones_entrega',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(), nullable=False),
        sa.Column('linea1', sa.String(), nullable=False),
        sa.Column('piso', sa.String(), nullable=True),
        sa.Column('departamento', sa.String(), nullable=True),
        sa.Column('ciudad', sa.String(), nullable=False),
        sa.Column('codigo_postal', sa.String(), nullable=False),
        sa.Column('referencia', sa.String(), nullable=True),
        sa.Column('es_principal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_direcciones_entrega_usuario_id_usuarios', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_direcciones_entrega'),
    )
    op.create_index('ix_direcciones_entrega_eliminado_en', 'direcciones_entrega', ['eliminado_en'])

    # Create categorias table
    op.create_table(
        'categorias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('padre_id', sa.Integer(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['padre_id'], ['categorias.id'], name='fk_categorias_padre_id_categorias'),
        sa.PrimaryKeyConstraint('id', name='pk_categorias'),
        sa.UniqueConstraint('nombre', name='uq_categorias_nombre'),
    )
    op.create_index('ix_categorias_nombre', 'categorias', ['nombre'], unique=True)
    op.create_index('ix_categorias_eliminado_en', 'categorias', ['eliminado_en'])

    # Create productos table
    op.create_table(
        'productos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('precio_base', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock_cantidad', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('disponible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('imagen_url', sa.String(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_productos'),
    )
    op.create_index('ix_productos_nombre', 'productos', ['nombre'])
    op.create_index('ix_productos_eliminado_en', 'productos', ['eliminado_en'])

    # Create ingredientes table
    op.create_table(
        'ingredientes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('es_alergeno', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_ingredientes'),
        sa.UniqueConstraint('nombre', name='uq_ingredientes_nombre'),
    )
    op.create_index('ix_ingredientes_nombre', 'ingredientes', ['nombre'], unique=True)

    # Create producto_categoria pivot table (N:M)
    op.create_table(
        'producto_categoria',
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], name='fk_producto_categoria_producto_id_productos', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], name='fk_producto_categoria_categoria_id_categorias', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('producto_id', 'categoria_id', name='pk_producto_categoria'),
    )

    # Create producto_ingrediente pivot table (N:M)
    op.create_table(
        'producto_ingrediente',
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('ingrediente_id', sa.Integer(), nullable=False),
        sa.Column('es_removible', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], name='fk_producto_ingrediente_producto_id_productos', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingrediente_id'], ['ingredientes.id'], name='fk_producto_ingrediente_ingrediente_id_ingredientes', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('producto_id', 'ingrediente_id', name='pk_producto_ingrediente'),
    )

    # Create pedidos table
    op.create_table(
        'pedidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('direccion_entrega_id', sa.Integer(), nullable=False),
        sa.Column('forma_pago_id', sa.Integer(), nullable=False),
        sa.Column('estado_pedido_id', sa.Integer(), nullable=False),
        sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('observacion', sa.String(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_pedidos_usuario_id_usuarios', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['direccion_entrega_id'], ['direcciones_entrega.id'], name='fk_pedidos_direccion_entrega_id_direcciones_entrega'),
        sa.ForeignKeyConstraint(['forma_pago_id'], ['formas_pago.id'], name='fk_pedidos_forma_pago_id_formas_pago'),
        sa.ForeignKeyConstraint(['estado_pedido_id'], ['estados_pedido.id'], name='fk_pedidos_estado_pedido_id_estados_pedido'),
        sa.PrimaryKeyConstraint('id', name='pk_pedidos'),
    )
    op.create_index('ix_pedidos_eliminado_en', 'pedidos', ['eliminado_en'])

    # Create detalle_pedido table
    op.create_table(
        'detalle_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('precio_snapshot', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('nombre_snapshot', sa.String(), nullable=False),
        sa.Column('ingredientes_excluidos', sa.String(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], name='fk_detalle_pedido_pedido_id_pedidos', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], name='fk_detalle_pedido_producto_id_productos', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_detalle_pedido'),
    )

    # Create historial_estado_pedido table (append-only audit)
    op.create_table(
        'historial_estado_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('estado_anterior_id', sa.Integer(), nullable=True),
        sa.Column('estado_nuevo_id', sa.Integer(), nullable=False),
        sa.Column('observacion', sa.String(), nullable=True),
        sa.Column('usuario_responsable_id', sa.Integer(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], name='fk_historial_estado_pedido_pedido_id_pedidos', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['estado_anterior_id'], ['estados_pedido.id'], name='fk_historial_estado_pedido_estado_anterior_id_estados_pedido'),
        sa.ForeignKeyConstraint(['estado_nuevo_id'], ['estados_pedido.id'], name='fk_historial_estado_pedido_estado_nuevo_id_estados_pedido'),
        sa.ForeignKeyConstraint(['usuario_responsable_id'], ['usuarios.id'], name='fk_historial_estado_pedido_usuario_responsable_id_usuarios'),
        sa.PrimaryKeyConstraint('id', name='pk_historial_estado_pedido'),
    )

    # Create pagos table
    op.create_table(
        'pagos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('mp_payment_id', sa.String(), nullable=True),
        sa.Column('mp_status', sa.String(), nullable=True),
        sa.Column('external_reference', sa.String(), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('gateway_response', sa.String(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], name='fk_pagos_pedido_id_pedidos', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_pagos'),
        sa.UniqueConstraint('mp_payment_id', name='uq_pagos_mp_payment_id'),
        sa.UniqueConstraint('idempotency_key', name='uq_pagos_idempotency_key'),
    )
    op.create_index('ix_pagos_mp_payment_id', 'pagos', ['mp_payment_id'], unique=True)
    op.create_index('ix_pagos_idempotency_key', 'pagos', ['idempotency_key'], unique=True)
    op.create_index('ix_pagos_eliminado_en', 'pagos', ['eliminado_en'])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign key dependencies)
    op.drop_table('pagos')
    op.drop_table('historial_estado_pedido')
    op.drop_table('detalle_pedido')
    op.drop_table('pedidos')
    op.drop_table('producto_ingrediente')
    op.drop_table('producto_categoria')
    op.drop_table('ingredientes')
    op.drop_table('productos')
    op.drop_table('categorias')
    op.drop_table('direcciones_entrega')
    op.drop_table('refresh_tokens')
    op.drop_table('usuarios')
    op.drop_table('formas_pago')
    op.drop_table('estados_pedido')
    op.drop_table('roles')
