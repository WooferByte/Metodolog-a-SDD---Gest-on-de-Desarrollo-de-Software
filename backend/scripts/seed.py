"""
Database seed script for initializing Food Store with default data.

This script implements idempotent seed logic using a get_or_create pattern:
- It safely runs multiple times without creating duplicates
- It checks for existing data before creating new records
- It uses database transactions to ensure data consistency

Usage:
    poetry run python backend/scripts/seed.py

Or from backend directory:
    python scripts/seed.py

Environment:
    Set SEED_DATABASE=true in .env to enable automatic seeding on app startup (future enhancement)
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory (backend) to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import engine, async_session_local, create_db_tables
from core.models import Rol, EstadoPedido, FormaPago, Usuario


async def get_or_create_rol(session: AsyncSession, nombre: str, descripcion: str = None) -> Rol:
    """
    Get an existing role or create it if not found.
    
    This implements the idempotent get_or_create pattern:
    - Queries for existing role by name
    - Returns it if found
    - Creates and returns new role if not found
    
    Args:
        session: AsyncSession for database operations
        nombre: Role name (unique)
        descripcion: Role description
    
    Returns:
        Rol: Existing or newly created role
    """
    # Query for existing role
    stmt = select(Rol).where(Rol.nombre == nombre)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        print(f"  [EXISTS] Rol '{nombre}' already exists (id={existing.id})")
        return existing
    
    # Create new role
    new_rol = Rol(nombre=nombre, descripcion=descripcion)
    session.add(new_rol)
    await session.flush()  # Get the ID without committing yet
    print(f"  [CREATE] Created Rol '{nombre}' (id={new_rol.id})")
    return new_rol


async def get_or_create_estado_pedido(
    session: AsyncSession, nombre: str, descripcion: str = None
) -> EstadoPedido:
    """
    Get an existing order status or create it if not found.
    
    Args:
        session: AsyncSession for database operations
        nombre: Status name (unique)
        descripcion: Status description
    
    Returns:
        EstadoPedido: Existing or newly created status
    """
    stmt = select(EstadoPedido).where(EstadoPedido.nombre == nombre)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        print(f"  [EXISTS] EstadoPedido '{nombre}' already exists (id={existing.id})")
        return existing
    
    new_estado = EstadoPedido(nombre=nombre, descripcion=descripcion)
    session.add(new_estado)
    await session.flush()
    print(f"  [CREATE] Created EstadoPedido '{nombre}' (id={new_estado.id})")
    return new_estado


async def get_or_create_forma_pago(
    session: AsyncSession, nombre: str, descripcion: str = None, activo: bool = True
) -> FormaPago:
    """
    Get an existing payment method or create it if not found.
    
    Args:
        session: AsyncSession for database operations
        nombre: Payment method name (unique)
        descripcion: Payment method description
        activo: Whether the payment method is active
    
    Returns:
        FormaPago: Existing or newly created payment method
    """
    stmt = select(FormaPago).where(FormaPago.nombre == nombre)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        print(f"  [EXISTS] FormaPago '{nombre}' already exists (id={existing.id})")
        return existing
    
    new_forma = FormaPago(nombre=nombre, descripcion=descripcion, activo=activo)
    session.add(new_forma)
    await session.flush()
    print(f"  [CREATE] Created FormaPago '{nombre}' (id={new_forma.id})")
    return new_forma


async def get_or_create_usuario(
    session: AsyncSession,
    email: str,
    nombre: str,
    password: str,
    rol_id: int,
    apellido: str = None,
) -> Usuario:
    """
    Get an existing user or create it if not found.
    
    Args:
        session: AsyncSession for database operations
        email: User email (unique identifier)
        nombre: User first name
        password: Plain text password (will be hashed)
        rol_id: Foreign key to Rol table
        apellido: User last name
    
    Returns:
        Usuario: Existing or newly created user
    """
    stmt = select(Usuario).where(Usuario.email == email)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        print(f"  [EXISTS] Usuario '{email}' already exists (id={existing.id})")
        return existing
    
    new_usuario = Usuario(
        email=email,
        nombre=nombre,
        apellido=apellido,
        hashed_password=Usuario.hash_password(password),
        rol_id=rol_id,
    )
    session.add(new_usuario)
    await session.flush()
    print(f"  [CREATE] Created Usuario '{email}' (id={new_usuario.id})")
    return new_usuario


async def seed_database():
    """
    Seed the database with essential data.
    
    Creates:
    1. Roles: ADMIN, STOCK, PEDIDOS, CLIENT
    2. Order statuses: PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO
    3. Payment methods: MERCADOPAGO, EFECTIVO, TRANSFERENCIA
    4. Admin user: admin@foodstore.com with ADMIN role
    
    This function is idempotent and can be run multiple times safely.
    Uses AsyncSession to maintain database connection pool and transaction safety.
    """
    print("\n" + "="*70)
    print("[SEED] Starting database seeding...")
    print("="*70 + "\n")
    
    # Create tables first
    print("[TABLE] Creating tables...")
    await create_db_tables()
    print("[OK] Tables created or verified\n")
    
    try:
        async with async_session_local() as session:
            # ===== SEED ROLES =====
            print("[ROLES] Seeding Roles...")
            rol_admin = await get_or_create_rol(
                session, "ADMIN", "Administrador del sistema con acceso total"
            )
            await get_or_create_rol(
                session, "STOCK", "Administrador de stock e inventario"
            )
            await get_or_create_rol(
                session, "PEDIDOS", "Encargado de gestión de pedidos"
            )
            await get_or_create_rol(
                session, "CLIENT", "Cliente de la tienda"
            )
            
            # ===== SEED ORDER STATUSES =====
            print("\n[STATUS] Seeding Order Statuses...")
            await get_or_create_estado_pedido(
                session, "PENDIENTE", "Pedido creado, en espera de confirmación"
            )
            await get_or_create_estado_pedido(
                session, "CONFIRMADO", "Pedido confirmado"
            )
            await get_or_create_estado_pedido(
                session, "EN_PREPARACIÓN", "Siendo preparado en el almacén"
            )
            await get_or_create_estado_pedido(
                session, "EN_CAMINO", "En camino hacia el cliente"
            )
            await get_or_create_estado_pedido(
                session, "ENTREGADO", "Entregado exitosamente"
            )
            await get_or_create_estado_pedido(
                session, "CANCELADO", "Pedido cancelado"
            )
            
            # ===== SEED PAYMENT METHODS =====
            print("\n[PAYMENT] Seeding Payment Methods...")
            await get_or_create_forma_pago(
                session, "MERCADOPAGO", "Pago a través de MercadoPago"
            )
            await get_or_create_forma_pago(
                session, "EFECTIVO", "Pago en efectivo"
            )
            await get_or_create_forma_pago(
                session, "TRANSFERENCIA", "Transferencia bancaria"
            )
            
            # ===== SEED ADMIN USER =====
            print("\n[USER] Seeding Admin User...")
            await get_or_create_usuario(
                session,
                email="admin@foodstore.com",
                nombre="Administrador",
                apellido="Sistema",
                password="admin123456",  # Change this in production!
                rol_id=rol_admin.id,
            )
            
            # Commit all changes
            await session.commit()
            print("\n" + "="*70)
            print("[SUCCESS] Database seeding completed successfully!")
            print("="*70 + "\n")
            
    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    """
    Entry point for running the seed script.
    
    Usage from backend directory:
        python scripts/seed.py
    
    Or using poetry:
        poetry run python scripts/seed.py
    """
    # On Windows, use SelectorEventLoop for psycopg compatibility
    if sys.platform == "win32":
        asyncio.run(
            seed_database(),
            loop_factory=asyncio.SelectorEventLoop
        )
    else:
        asyncio.run(seed_database())
