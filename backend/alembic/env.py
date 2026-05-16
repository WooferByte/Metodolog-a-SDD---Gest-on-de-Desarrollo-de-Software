"""
Alembic environment script for async SQLAlchemy migrations.

This script handles both offline and online migration modes with async support.
It loads SQLModel metadata to auto-detect schema changes.
"""
import asyncio
import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Add backend directory to path so we can import from core module
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import all models to register with SQLAlchemy metadata
from core.models import (  # noqa: F401, E402
    Rol,
    EstadoPedido,
    FormaPago,
    Usuario,
    RefreshToken,
    DireccionEntrega,
    Categoria,
    Producto,
    Ingrediente,
    ProductoCategoria,
    ProductoIngrediente,
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
    Pago,
)

# Import SQLModel to get metadata
from sqlmodel import SQLModel  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Set the target_metadata for Alembic's autogenerate feature
target_metadata = SQLModel.metadata

# Naming conventions for consistent constraint naming
naming_conventions = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Apply naming conventions to metadata
target_metadata.naming_convention = naming_conventions


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.  By skipping the
    Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        version_num_col_length=255,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run the actual migrations using the provided connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        version_num_col_length=255,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    # Use sync driver for migration generation, async for actual operations
    db_url = configuration.get("sqlalchemy.url", "").replace(
        "postgresql+asyncpg://", "postgresql+psycopg://", 1
    )

    if not db_url:
        logger.warning("No database URL configured, using offline mode")
        run_migrations_offline()
        return

    try:
        connectable = create_async_engine(
            db_url,
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()
    except Exception as e:
        logger.warning(f"Could not connect to database: {e}. Using offline mode.")
        run_migrations_offline()


if context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    # On Windows, use SelectorEventLoop for psycopg compatibility
    if sys.platform == "win32":
        try:
            asyncio.run(run_migrations_online(), loop_factory=asyncio.SelectorEventLoop)
        except Exception:
            logger.info("Falling back to offline mode due to connection issues")
            run_migrations_offline()
    else:
        try:
            asyncio.run(run_migrations_online())
        except Exception:
            logger.info("Falling back to offline mode due to connection issues")
            run_migrations_offline()
