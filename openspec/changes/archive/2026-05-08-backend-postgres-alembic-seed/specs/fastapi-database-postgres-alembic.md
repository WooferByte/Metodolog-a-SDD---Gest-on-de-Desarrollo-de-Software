# Specification: FastAPI Database PostgreSQL Alembic

Database connectivity, async engine configuration, and Alembic migration framework.

## ADDED Requirements

### Requirement: PostgreSQL Connection with Async Engine

The system SHALL establish a PostgreSQL connection pool using async SQLAlchemy engine to enable non-blocking database operations in FastAPI.

#### Scenario: Connect to PostgreSQL with asyncpg driver
- **WHEN** FastAPI application starts
- **THEN** async engine is created with `postgresql+asyncpg://user:password@host:5432/foodstore` URI
- **AND** connection pool is initialized with min 5, max 20 connections

#### Scenario: Environment-based database URL configuration
- **WHEN** application reads `settings.DATABASE_URL` from environment
- **THEN** connection string supports local development (`localhost:5432`) and production (`managed PostgreSQL host`)
- **AND** credentials are never hardcoded; use `.env` file in development

### Requirement: Alembic Migrations with Async Context

The system SHALL use Alembic as version control for database schema changes, with async-compatible context manager.

#### Scenario: Initialize Alembic project structure
- **WHEN** developer runs `alembic init alembic`
- **THEN** directory structure created: `alembic/` with `versions/`, `env.py`, `script.py.mako`, `alembic.ini`
- **AND** `alembic.ini` configured with `sqlalchemy.url = postgresql+asyncpg://...`

#### Scenario: Run migrations in async context
- **WHEN** `alembic upgrade head` executed
- **THEN** `alembic/env.py` uses `asyncio.run(run_async_migrations())` to run migrations without blocking
- **AND** all migration functions are defined as async coroutines

#### Scenario: Track migration state
- **WHEN** migration completes successfully
- **THEN** migration record inserted into `alembic_version` table with version hash
- **AND** subsequent `alembic upgrade head` sees no pending migrations

### Requirement: Initial Migration Creates All 15 Tables

The system SHALL generate and apply initial migration that creates complete database schema with 15 tables.

#### Scenario: Auto-generate migration from SQLModel metadata
- **WHEN** developer runs `alembic revision --autogenerate -m "Initial schema creation"`
- **THEN** Alembic generates migration file `alembic/versions/<timestamp>_initial_schema_creation.py`
- **AND** migration includes CREATE TABLE statements for all 15 entities

#### Scenario: Verify migration creates complete schema
- **WHEN** `alembic upgrade head` executed on empty database
- **THEN** all 15 tables present: usuario, rol, refresh_token, direccion_entrega, categoria, producto, ingrediente, producto_categoria, producto_ingrediente, estado_pedido, pedido, detalle_pedido, historial_estado_pedido, forma_pago, pago
- **AND** all columns, constraints, indexes created per SQLModel definitions

#### Scenario: Migration includes proper naming conventions
- **WHEN** migration script generated
- **THEN** primary keys follow pattern `id` (auto-increment serial)
- **AND** foreign keys follow pattern `<table>_<refcolumn>_fk` (e.g., `usuario_rol_id_fk`)
- **AND** indexes follow pattern `ix_<table>_<columns>` (e.g., `ix_usuario_email`)

### Requirement: Soft Delete Pattern Implementation

The system SHALL support soft deletion with `eliminado_en` timestamp field; deleted rows invisible in normal queries.

#### Scenario: Add soft delete field to mutable entities
- **WHEN** SQLModel entity defined (e.g., Usuario, Producto)
- **THEN** entity includes field: `eliminado_en: Optional[datetime] = None`
- **AND** column created with `DEFAULT NULL` and index on `eliminado_en` for filtering

#### Scenario: Soft delete query filter
- **WHEN** repository queries active entities (e.g., `list_usuarios()`)
- **THEN** query includes filter: `WHERE eliminado_en IS NULL`
- **AND** soft-deleted rows never appear unless explicitly requested

#### Scenario: Soft delete operation
- **WHEN** soft delete method called (e.g., `usuario.soft_delete()`)
- **THEN** `eliminado_en` set to current UTC timestamp
- **AND** row remains in database; physically unchanged except for timestamp
- **AND** row invisible to normal queries (except audits/admins)

#### Scenario: Audit trail preservation
- **WHEN** row soft deleted
- **THEN** `creado_en` and `actualizado_en` unchanged (immutable)
- **AND** admin can query `WHERE eliminado_en IS NOT NULL` to view deleted rows
- **AND** hard delete never occurs in normal operations (regulatory compliance)
