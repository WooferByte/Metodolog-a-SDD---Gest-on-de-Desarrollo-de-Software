"""
Database layer with SQLAlchemy async engine and session management.

Provides:
- AsyncSession factory for FastAPI dependency injection
- Connection pooling with configurable limits
- Unit of Work pattern support (prep for CHANGE 4)
- Table creation utilities
"""
from typing import AsyncGenerator

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlmodel import SQLModel

from core.config import settings


# Create async SQLAlchemy engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.is_dev(),  # Log SQL in development
    future=True,
    pool_pre_ping=True,  # Verify connections before using them
    # Use AsyncAdaptedQueuePool for async connections (not NullPool)
    poolclass=NullPool if settings.is_test() else AsyncAdaptedQueuePool,
    # Connection pool settings
    pool_size=settings.database_pool_size if not settings.is_test() else 1,
    max_overflow=settings.database_max_overflow if not settings.is_test() else 0,
)


# Create async session factory
async_session_local = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session injection.
    
    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Active database session for the request lifetime
    
    Raises:
        DatabaseError: If connection fails during request
    """
    async with async_session_local() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Unit of Work pattern support for CHANGE 4.
    
    Creates a new session that spans the entire request context,
    allowing multiple repositories to share the same transaction.
    
    Usage (future):
        uow = await get_db_context()
        try:
            async with uow.session() as session:
                # Multiple repository operations
                user_repo = UserRepository(session)
                order_repo = OrderRepository(session)
                await user_repo.save(user)
                await order_repo.save(order)
            await uow.commit()
        except Exception:
            await uow.rollback()
    
    Yields:
        AsyncSession: Active database session for the context
    """
    async with async_session_local() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """
    Test database connectivity.
    
    Called during application startup to verify the database is accessible.
    
    Returns:
        bool: True if connection successful, False otherwise
        
    Raises:
        Exception: If connection fails (logged in startup event)
    """
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False


async def close_db_connection() -> None:
    """
    Close database engine and connection pools.
    
    Called during application shutdown.
    Ensures all connections are properly released.
    """
    await engine.dispose()


async def create_db_tables() -> None:
    """
    Create all database tables defined in SQLModel models.
    
    Called during application startup or by the seed script.
    Uses SQLAlchemy metadata to create tables that don't exist.
    
    This function:
    - Imports all models to ensure they're registered
    - Creates tables based on model definitions
    - Is idempotent (safe to call multiple times)
    """
    # Import models to register them with SQLAlchemy metadata
    from core.models import Rol, EstadoPedido, FormaPago, Usuario  # noqa: F401
    
    # Create all tables defined in models
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


