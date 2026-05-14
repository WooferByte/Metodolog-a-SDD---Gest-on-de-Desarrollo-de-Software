"""
seed_dev_data.py — Carga datos de desarrollo en todas las tablas.

Requiere que seed.py haya corrido antes (roles, estados_pedido, formas_pago, admin user).

Uso (desde backend/):
    python scripts/seed_dev_data.py

Datos creados: 5 registros por tabla, cubriendo todas las columnas.
El script es idempotente: verifica existencia antes de insertar.
"""
import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from core.config import settings
from core.models import (
    Categoria,
    DetallePedido,
    DireccionEntrega,
    HistorialEstadoPedido,
    Ingrediente,
    Pago,
    Pedido,
    Producto,
    ProductoCategoria,
    ProductoIngrediente,
    RefreshToken,
    Rol,
    Usuario,
    UsuarioRol,
    FormaPago,
    EstadoPedido,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime.utcnow()


async def get_or_skip(session: AsyncSession, model, **filters):
    """Return existing record or None. Print status."""
    stmt = select(model)
    for attr, val in filters.items():
        stmt = stmt.where(getattr(model, attr) == val)
    result = await session.execute(stmt)
    return result.scalars().first()


def _sep(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


async def seed_usuarios(session: AsyncSession) -> list[Usuario]:
    _sep("USUARIOS (5)")
    data = [
        dict(email="admin@foodstore.com",   nombre="Administrador", apellido="Sistema",    password="admin123456",   telefono="+54 11 1234-5678"),
        dict(email="stock@foodstore.com",   nombre="Carlos",        apellido="López",       password="stock123456",   telefono="+54 11 2345-6789"),
        dict(email="pedidos@foodstore.com", nombre="María",         apellido="González",    password="pedidos123456", telefono="+54 11 3456-7890"),
        dict(email="cliente1@test.com",     nombre="Juan",          apellido="Martínez",    password="cliente123456", telefono="+54 11 4567-8901"),
        dict(email="cliente2@test.com",     nombre="Laura",         apellido="Rodríguez",   password="cliente123456", telefono="+54 11 5678-9012"),
    ]
    usuarios = []
    for d in data:
        existing = await get_or_skip(session, Usuario, email=d["email"])
        if existing:
            print(f"  [EXISTS] {d['email']} (id={existing.id})")
            usuarios.append(existing)
            continue
        u = Usuario(
            email=d["email"],
            nombre=d["nombre"],
            apellido=d["apellido"],
            hashed_password=Usuario.hash_password(d["password"]),
            activo=True,
            telefono=d["telefono"],
            ultimo_login=NOW - timedelta(hours=1),
            creado_en=NOW,
            actualizado_en=NOW,
            eliminado_en=None,
        )
        session.add(u)
        await session.flush()
        print(f"  [CREATE] {u.email} (id={u.id})")
        usuarios.append(u)
    return usuarios


async def seed_usuario_roles(session: AsyncSession, usuarios: list[Usuario]) -> None:
    _sep("USUARIO_ROL")
    # admin->ADMIN(1), stock->STOCK(2), pedidos->PEDIDOS(3), cliente1->CLIENT(4), cliente2->CLIENT(4)
    rol_ids = [1, 2, 3, 4, 4]
    for usuario, rol_id in zip(usuarios, rol_ids):
        stmt = select(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario.id,
            UsuarioRol.rol_id == rol_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            print(f"  [EXISTS] usuario_id={usuario.id} -> rol_id={rol_id}")
            continue
        ur = UsuarioRol(usuario_id=usuario.id, rol_id=rol_id)
        session.add(ur)
        print(f"  [CREATE] usuario_id={usuario.id} ({usuario.email}) -> rol_id={rol_id}")
    await session.flush()


async def seed_refresh_tokens(session: AsyncSession, usuarios: list[Usuario]) -> None:
    _sep("REFRESH_TOKENS (5)")
    for i, usuario in enumerate(usuarios):
        token_val = f"dev-refresh-token-{i+1}-{uuid.uuid4().hex[:8]}"
        existing = await get_or_skip(session, RefreshToken, usuario_id=usuario.id)
        if existing:
            print(f"  [EXISTS] usuario_id={usuario.id}")
            continue
        rt = RefreshToken(
            usuario_id=usuario.id,
            token=token_val,
            expires_at=NOW + timedelta(days=7),
            revoked_at=None if i < 4 else NOW - timedelta(hours=1),
            creado_en=NOW,
        )
        session.add(rt)
        await session.flush()
        print(f"  [CREATE] token para {usuario.email} (id={rt.id}, revocado={'Sí' if rt.revoked_at else 'No'})")


async def seed_categorias(session: AsyncSession) -> list[Categoria]:
    _sep("CATEGORIAS (5)")
    raices = [
        dict(nombre="Pizzas",        descripcion="Pizzas artesanales con masa fresca"),
        dict(nombre="Hamburguesas",  descripcion="Hamburguesas gourmet de autor"),
        dict(nombre="Bebidas",       descripcion="Gaseosas, jugos y bebidas sin alcohol"),
        dict(nombre="Postres",       descripcion="Tortas, brownies y alfajores"),
    ]
    categorias = []
    for d in raices:
        existing = await get_or_skip(session, Categoria, nombre=d["nombre"])
        if existing:
            print(f"  [EXISTS] {d['nombre']} (id={existing.id})")
            categorias.append(existing)
            continue
        c = Categoria(
            nombre=d["nombre"],
            descripcion=d["descripcion"],
            padre_id=None,
            creado_en=NOW,
            actualizado_en=NOW,
            eliminado_en=None,
        )
        session.add(c)
        await session.flush()
        print(f"  [CREATE] {c.nombre} (id={c.id}, raíz)")
        categorias.append(c)

    # 5ta categoría: subcategoría hija de Pizzas
    existing = await get_or_skip(session, Categoria, nombre="Pizzas Clásicas")
    if existing:
        print(f"  [EXISTS] Pizzas Clásicas (id={existing.id})")
        categorias.append(existing)
    else:
        sub = Categoria(
            nombre="Pizzas Clásicas",
            descripcion="Variedades clásicas italianas",
            padre_id=categorias[0].id,
            creado_en=NOW,
            actualizado_en=NOW,
            eliminado_en=None,
        )
        session.add(sub)
        await session.flush()
        print(f"  [CREATE] {sub.nombre} (id={sub.id}, padre_id={sub.padre_id})")
        categorias.append(sub)

    return categorias


async def seed_ingredientes(session: AsyncSession) -> list[Ingrediente]:
    _sep("INGREDIENTES (5)")
    data = [
        dict(nombre="Tomate",             es_alergeno=False),
        dict(nombre="Queso Mozzarella",   es_alergeno=True),
        dict(nombre="Harina de Trigo",    es_alergeno=True),
        dict(nombre="Carne Vacuna",       es_alergeno=False),
        dict(nombre="Maíz",              es_alergeno=False),
    ]
    ingredientes = []
    for d in data:
        existing = await get_or_skip(session, Ingrediente, nombre=d["nombre"])
        if existing:
            print(f"  [EXISTS] {d['nombre']} (id={existing.id})")
            ingredientes.append(existing)
            continue
        ing = Ingrediente(
            nombre=d["nombre"],
            es_alergeno=d["es_alergeno"],
            creado_en=NOW,
            eliminado_en=None,
        )
        session.add(ing)
        await session.flush()
        print(f"  [CREATE] {ing.nombre} (id={ing.id}, alergeno={ing.es_alergeno})")
        ingredientes.append(ing)
    return ingredientes


async def seed_productos(session: AsyncSession) -> list[Producto]:
    _sep("PRODUCTOS (5)")
    data = [
        dict(nombre="Pizza Margherita",    descripcion="Tomate, mozzarella y albahaca fresca",        precio=Decimal("1800.00"), stock=15, disponible=True,  imagen_url="https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&q=80"),
        dict(nombre="Hamburguesa Clásica", descripcion="Carne 200g, lechuga, tomate y aderezo",      precio=Decimal("1500.00"), stock=20, disponible=True,  imagen_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&q=80"),
        dict(nombre="Coca Cola 500ml",     descripcion="Gaseosa Coca Cola botella 500ml",            precio=Decimal("600.00"),  stock=50, disponible=True,  imagen_url="https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&q=80"),
        dict(nombre="Brownie de Chocolate",descripcion="Brownie húmedo con nueces y chips de choco", precio=Decimal("800.00"),  stock=10, disponible=True,  imagen_url="https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400&q=80"),
        dict(nombre="Empanadas x6",        descripcion="Seis empanadas de carne cortada a cuchillo", precio=Decimal("1200.00"), stock=25, disponible=False, imagen_url="https://images.unsplash.com/photo-1605629921711-2f6b00c6bbf4?w=400&q=80"),
    ]
    productos = []
    for d in data:
        existing = await get_or_skip(session, Producto, nombre=d["nombre"])
        if existing:
            print(f"  [EXISTS] {d['nombre']} (id={existing.id})")
            productos.append(existing)
            continue
        p = Producto(
            nombre=d["nombre"],
            descripcion=d["descripcion"],
            precio_base=d["precio"],
            stock_cantidad=d["stock"],
            disponible=d["disponible"],
            imagen_url=d["imagen_url"],
            creado_en=NOW,
            actualizado_en=NOW,
            eliminado_en=None,
        )
        session.add(p)
        await session.flush()
        print(f"  [CREATE] {p.nombre} (id={p.id}, precio=${p.precio_base}, stock={p.stock_cantidad})")
        productos.append(p)
    return productos


async def seed_producto_categoria(
    session: AsyncSession,
    productos: list[Producto],
    categorias: list[Categoria],
) -> None:
    _sep("PRODUCTO_CATEGORIA (5)")
    # pizzas[0]=Pizzas, [1]=Hamburguesas, [2]=Bebidas, [3]=Postres, [4]=Pizzas Clásicas
    pairs = [
        (productos[0], categorias[0]),   # Pizza -> Pizzas
        (productos[0], categorias[4]),   # Pizza -> Pizzas Clásicas
        (productos[1], categorias[1]),   # Hamburguesa -> Hamburguesas
        (productos[2], categorias[2]),   # Coca Cola -> Bebidas
        (productos[3], categorias[3]),   # Brownie -> Postres
    ]
    for prod, cat in pairs:
        stmt = select(ProductoCategoria).where(
            ProductoCategoria.producto_id == prod.id,
            ProductoCategoria.categoria_id == cat.id,
        )
        if (await session.execute(stmt)).scalar_one_or_none():
            print(f"  [EXISTS] prod_id={prod.id} -> cat_id={cat.id}")
            continue
        pc = ProductoCategoria(producto_id=prod.id, categoria_id=cat.id)
        session.add(pc)
        print(f"  [CREATE] {prod.nombre} -> {cat.nombre}")
    await session.flush()


async def seed_producto_ingrediente(
    session: AsyncSession,
    productos: list[Producto],
    ingredientes: list[Ingrediente],
) -> None:
    _sep("PRODUCTO_INGREDIENTE (5)")
    # ing[0]=Tomate, [1]=Mozzarella, [2]=Harina, [3]=Carne, [4]=Maíz
    pairs = [
        (productos[0], ingredientes[0], True),   # Pizza -> Tomate (removible)
        (productos[0], ingredientes[1], True),   # Pizza -> Mozzarella (removible)
        (productos[0], ingredientes[2], False),  # Pizza -> Harina (no removible)
        (productos[1], ingredientes[3], False),  # Hamburguesa -> Carne (no removible)
        (productos[1], ingredientes[4], True),   # Hamburguesa -> Maíz (removible)
    ]
    for prod, ing, removible in pairs:
        stmt = select(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == prod.id,
            ProductoIngrediente.ingrediente_id == ing.id,
        )
        if (await session.execute(stmt)).scalar_one_or_none():
            print(f"  [EXISTS] prod_id={prod.id} -> ing_id={ing.id}")
            continue
        pi = ProductoIngrediente(
            producto_id=prod.id,
            ingrediente_id=ing.id,
            es_removible=removible,
        )
        session.add(pi)
        print(f"  [CREATE] {prod.nombre} -> {ing.nombre} (removible={removible})")
    await session.flush()


async def seed_direcciones(
    session: AsyncSession, usuarios: list[Usuario]
) -> list[DireccionEntrega]:
    _sep("DIRECCIONES_ENTREGA (5)")
    # 2 para cliente1, 2 para cliente2, 1 para admin
    data = [
        dict(usuario=usuarios[0], alias="Oficina",   linea1="Av. Corrientes 1234",  piso="3",    dpto="B", ciudad="Buenos Aires", cp="C1043",  ref="Edificio azul",    principal=True),
        dict(usuario=usuarios[3], alias="Casa",       linea1="Av. Santa Fe 567",     piso=None,   dpto=None,ciudad="Buenos Aires", cp="C1059",  ref="Timbre 3B",        principal=True),
        dict(usuario=usuarios[3], alias="Trabajo",    linea1="Reconquista 890",      piso="10",   dpto="A", ciudad="Buenos Aires", cp="C1003",  ref="Piso 10 of. A",    principal=False),
        dict(usuario=usuarios[4], alias="Casa",       linea1="Rivadavia 2345",       piso=None,   dpto=None,ciudad="Buenos Aires", cp="C1034",  ref="Casa blanca",      principal=True),
        dict(usuario=usuarios[4], alias="Facultad",   linea1="Av. Las Heras 2214",   piso=None,   dpto=None,ciudad="Buenos Aires", cp="C1127",  ref="Portón negro",     principal=False),
    ]
    direcciones = []
    for d in data:
        stmt = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == d["usuario"].id,
            DireccionEntrega.alias == d["alias"],
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            print(f"  [EXISTS] {d['usuario'].email} — {d['alias']} (id={existing.id})")
            direcciones.append(existing)
            continue
        dir_ = DireccionEntrega(
            usuario_id=d["usuario"].id,
            alias=d["alias"],
            linea1=d["linea1"],
            piso=d["piso"],
            departamento=d["dpto"],
            ciudad=d["ciudad"],
            codigo_postal=d["cp"],
            referencia=d["ref"],
            es_predeterminada=d["principal"],
            creado_en=NOW,
            actualizado_en=NOW,
            eliminado_en=None,
        )
        session.add(dir_)
        await session.flush()
        print(f"  [CREATE] {d['usuario'].email} — {dir_.alias} (id={dir_.id}, predeterminada={dir_.es_predeterminada})")
        direcciones.append(dir_)
    return direcciones


async def seed_pedidos(
    session: AsyncSession,
    usuarios: list[Usuario],
    direcciones: list[DireccionEntrega],
) -> list[Pedido]:
    _sep("PEDIDOS (5)")
    # formas_pago: 1=MERCADOPAGO, 2=EFECTIVO, 3=TRANSFERENCIA
    # estados:     1=PENDIENTE, 2=CONFIRMADO, 3=EN_PREP, 4=EN_CAMINO, 5=ENTREGADO, 6=CANCELADO
    data = [
        dict(usuario=usuarios[3], dir_idx=1, forma_pago_id=1, estado_id=1, total=Decimal("3600.00"), obs="Sin cebolla por favor",       dir_snap='{"linea1": "Av. Santa Fe 567", "ciudad": "Buenos Aires"}'),
        dict(usuario=usuarios[3], dir_idx=2, forma_pago_id=2, estado_id=2, total=Decimal("1500.00"), obs=None,                          dir_snap='{"linea1": "Reconquista 890", "ciudad": "Buenos Aires"}'),
        dict(usuario=usuarios[4], dir_idx=3, forma_pago_id=1, estado_id=3, total=Decimal("2400.00"), obs="Llamar al llegar",             dir_snap='{"linea1": "Rivadavia 2345", "ciudad": "Buenos Aires"}'),
        dict(usuario=usuarios[4], dir_idx=4, forma_pago_id=3, estado_id=5, total=Decimal("800.00"),  obs=None,                          dir_snap='{"linea1": "Av. Las Heras 2214", "ciudad": "Buenos Aires"}'),
        dict(usuario=usuarios[3], dir_idx=1, forma_pago_id=1, estado_id=6, total=Decimal("1200.00"), obs="Cancelado por el cliente",    dir_snap='{"linea1": "Av. Santa Fe 567", "ciudad": "Buenos Aires"}'),
    ]
    pedidos = []
    for i, d in enumerate(data):
        dir_obj = direcciones[d["dir_idx"]]
        stmt = select(Pedido).where(
            Pedido.usuario_id == d["usuario"].id,
            Pedido.total == d["total"],
            Pedido.estado_pedido_id == d["estado_id"],
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            print(f"  [EXISTS] pedido_id={existing.id}")
            pedidos.append(existing)
            continue
        p = Pedido(
            usuario_id=d["usuario"].id,
            direccion_entrega_id=dir_obj.id,
            forma_pago_id=d["forma_pago_id"],
            estado_pedido_id=d["estado_id"],
            total=d["total"],
            observacion=d["obs"],
            direccion_snapshot=d["dir_snap"],
            creado_en=NOW - timedelta(hours=(5 - i)),
            actualizado_en=NOW - timedelta(minutes=(5 - i) * 10),
            eliminado_en=None,
        )
        session.add(p)
        await session.flush()
        print(f"  [CREATE] pedido_id={p.id} | usuario={d['usuario'].email} | estado_id={p.estado_pedido_id} | total=${p.total}")
        pedidos.append(p)
    return pedidos


async def seed_detalle_pedido(
    session: AsyncSession,
    pedidos: list[Pedido],
    productos: list[Producto],
) -> None:
    _sep("DETALLE_PEDIDO (5)")
    # Una línea por pedido, con ingredientes_excluidos variados
    data = [
        dict(pedido=pedidos[0], prod=productos[0], cant=2, excluidos=[2]),       # Pizza x2, sin mozzarella
        dict(pedido=pedidos[1], prod=productos[1], cant=1, excluidos=None),      # Hamburguesa x1
        dict(pedido=pedidos[2], prod=productos[2], cant=4, excluidos=None),      # Coca Cola x4
        dict(pedido=pedidos[3], prod=productos[3], cant=1, excluidos=None),      # Brownie x1
        dict(pedido=pedidos[4], prod=productos[4], cant=1, excluidos=[4, 5]),    # Empanadas x1, sin carne ni maíz
    ]
    for d in data:
        stmt = select(DetallePedido).where(
            DetallePedido.pedido_id == d["pedido"].id,
            DetallePedido.producto_id == d["prod"].id,
        )
        if (await session.execute(stmt)).scalar_one_or_none():
            print(f"  [EXISTS] pedido_id={d['pedido'].id} -> prod_id={d['prod'].id}")
            continue
        det = DetallePedido(
            pedido_id=d["pedido"].id,
            producto_id=d["prod"].id,
            cantidad=d["cant"],
            precio_snapshot=d["prod"].precio_base,
            nombre_snapshot=d["prod"].nombre,
            ingredientes_excluidos=d["excluidos"],
            creado_en=d["pedido"].creado_en,
        )
        session.add(det)
        await session.flush()
        print(f"  [CREATE] detalle_id={det.id} | {d['prod'].nombre} x{d['cant']} | excluidos={d['excluidos']}")


async def seed_historial_estados(
    session: AsyncSession,
    pedidos: list[Pedido],
    usuarios: list[Usuario],
) -> None:
    _sep("HISTORIAL_ESTADO_PEDIDO (5)")
    # Una entrada inicial por pedido (NULL -> estado actual)
    for i, pedido in enumerate(pedidos):
        responsable = usuarios[0] if i % 2 == 0 else usuarios[1]
        stmt = select(HistorialEstadoPedido).where(
            HistorialEstadoPedido.pedido_id == pedido.id,
        )
        if (await session.execute(stmt)).scalar_one_or_none():
            print(f"  [EXISTS] pedido_id={pedido.id}")
            continue
        h = HistorialEstadoPedido(
            pedido_id=pedido.id,
            estado_anterior_id=None,
            estado_nuevo_id=pedido.estado_pedido_id,
            observacion=f"Pedido #{pedido.id} creado en estado inicial",
            usuario_responsable_id=responsable.id,
            creado_en=pedido.creado_en,
        )
        session.add(h)
        await session.flush()
        print(f"  [CREATE] historial_id={h.id} | pedido_id={pedido.id} | NULL -> estado_id={h.estado_nuevo_id}")


async def seed_pagos(
    session: AsyncSession, pedidos: list[Pedido]
) -> None:
    _sep("PAGOS (5)")
    mp_statuses = ["pending", "approved", "in_process", "approved", "cancelled"]
    for i, pedido in enumerate(pedidos):
        stmt = select(Pago).where(Pago.pedido_id == pedido.id)
        if (await session.execute(stmt)).scalar_one_or_none():
            print(f"  [EXISTS] pedido_id={pedido.id}")
            continue
        ext_ref = str(uuid.uuid4())
        idempotency = str(uuid.uuid4())
        pago = Pago(
            pedido_id=pedido.id,
            mp_payment_id=f"MP_DEV_{i+1:04d}",
            mp_status=mp_statuses[i],
            external_reference=ext_ref,
            idempotency_key=idempotency,
            gateway_response='{"status": "' + mp_statuses[i] + '", "detail": "dev seed"}',
            creado_en=pedido.creado_en + timedelta(minutes=1),
            actualizado_en=pedido.actualizado_en,
            eliminado_en=None,
        )
        session.add(pago)
        await session.flush()
        print(f"  [CREATE] pago_id={pago.id} | pedido_id={pedido.id} | mp_status={pago.mp_status}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def seed_all() -> None:
    print("\n" + "=" * 60)
    print("  SEED DEV DATA — Food Store")
    print("=" * 60)

    engine = create_async_engine(settings.database_url, echo=False)

    async with AsyncSession(engine) as session:
        async with session.begin():
            usuarios   = await seed_usuarios(session)
            await seed_usuario_roles(session, usuarios)
            await seed_refresh_tokens(session, usuarios)
            categorias = await seed_categorias(session)
            ingredientes = await seed_ingredientes(session)
            productos  = await seed_productos(session)
            await seed_producto_categoria(session, productos, categorias)
            await seed_producto_ingrediente(session, productos, ingredientes)
            direcciones = await seed_direcciones(session, usuarios)
            pedidos    = await seed_pedidos(session, usuarios, direcciones)
            await seed_detalle_pedido(session, pedidos, productos)
            await seed_historial_estados(session, pedidos, usuarios)
            await seed_pagos(session, pedidos)

    await engine.dispose()

    print("\n" + "=" * 60)
    print("  [SUCCESS] Dev data seeded correctamente.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_all())
