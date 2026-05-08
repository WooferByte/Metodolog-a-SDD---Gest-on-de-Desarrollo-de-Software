# PostgreSQL Database with Alembic Migrations and Seed Data

## Summary

This change establishes the foundational PostgreSQL database layer for FoodStore with a comprehensive 15-table schema, Alembic-based migration framework, and idempotent seed data. This is a core infrastructure component that enables all subsequent backend features.

## Motivation

The backend requires a robust, production-ready database foundation that:
- Tracks complete audit history (created, updated, deleted timestamps)
- Supports soft deletes for data retention compliance
- Provides version control for schema migrations
- Includes reference data (roles, order states, payment methods)
- Follows domain-driven design principles

Without this, the FastAPI backend cannot persist data or enforce business logic at the database level.

## What

### Entity Relationship Diagram v5
A normalized PostgreSQL schema with 15 tables organized in 3 bounded domains:

**Domain 1: Auth + Users** (4 tables)
- `usuario` — login credentials, profile, soft delete
- `rol` — immutable enum: ADMIN, STOCK, PEDIDOS, CLIENT
- `refresh_token` — JWT refresh tracking with revocation
- `direccion_entrega` — user delivery addresses

**Domain 2: Products + Catalog** (5 tables)
- `categoria` — product categories with hierarchical self-reference
- `producto` — inventory with price, stock, availability, soft delete
- `ingrediente` — food items, allergen tracking
- `producto_categoria` — N:M product-category mapping
- `producto_ingrediente` — N:M product-ingredient mapping with `es_removible`

**Domain 3: Orders + Payments** (6 tables)
- `estado_pedido` — 6 immutable order states (PENDIENTE, CONFIRMADO, PREPARANDO, LISTO, ENTREGADO, CANCELADO)
- `pedido` — order header with FSM state tracking and snapshots
- `detalle_pedido` — line items with price/name snapshots and excluded ingredients
- `historial_estado_pedido` — append-only audit trail (never updated)
- `pago` — payment records with MercadoPago transaction tracking
- `forma_pago` — payment method enum (EFECTIVO, MERCADOPAGO, TARJETA)

### Alembic Migration Framework
- Async-compatible context manager for FastAPI integration
- Automatic naming conventions (PK, FK, IX, CK prefixes)
- Version-controlled schema evolution from initial state
- Rollback capability for each migration

### Idempotent Seed Script
- `scripts/seed.py` — loads immutable reference data
- Gets or creates pattern to prevent duplicates on re-runs
- Populates: roles, order states, payment methods, admin user
- Integrates with async SQLAlchemy session management

## Benefits

1. **Version Control for Schema** — Track all database changes in git; easy rollback and peer review
2. **Audit Trail** — `creado_en`, `actualizado_en`, `eliminado_en` fields on all mutable entities for compliance
3. **Soft Deletes** — `eliminado_en` field allows logical deletion without losing historical data
4. **Price Snapshots** — Order details store product name and price at order time, preventing retroactive changes
5. **Append-Only History** — OrderHistory never updated, ensuring immutable audit trail for regulatory audits
6. **Domain-Driven Structure** — Clear separation of Auth, Products, Orders concerns with proper FK constraints
7. **Idempotent Seeding** — Run seed script multiple times safely without duplicate errors

## Dependencies

### On CHANGE 2: backend-fastapi-core-setup ✅
- Requires `backend/core/config.py` for database URL and async engine config
- Requires poetry lock file with sqlalchemy, alembic, psycopg[binary] dependencies
- Requires FastAPI application structure (backend/app.py)
- Alembic migrations must be compatible with FastAPI's async context

## Capabilities

This change introduces or modifies these capabilities:

1. **fastapi-database-postgres-alembic** — PostgreSQL connection, async engine, Alembic setup
2. **domain-entities-user-auth** — Usuario, Rol, RefreshToken, DireccionEntrega models
3. **domain-entities-products-catalog** — Categoria, Producto, Ingrediente, pivot tables
4. **domain-entities-orders-payments** — EstadoPedido, Pedido, DetallePedido, HistorialEstadoPedido, Pago

## Estimate

~2 hours of implementation:
- Alembic setup: 15 min
- Define 15 SQLModel entities: 45 min
- Generate and review migration: 10 min
- Test and seed verification: 20 min (plus local PostgreSQL startup time)

## User Stories Affected

- **US-000b: Database, Migrations, Seed Data** — Core requirement for all backend operations

## Success Criteria

- ✅ All 15 tables created in PostgreSQL
- ✅ Alembic migration history tracked in `alembic_version` table
- ✅ Seed script loads 4 roles, 6 order states, 3 payment methods, 1 admin user
- ✅ Soft delete queries exclude `eliminado_en IS NOT NULL` rows
- ✅ Order details retain price/name snapshots after product modifications
- ✅ Audit fields (`creado_en`, `actualizado_en`) populated on all mutations
- ✅ No foreign key constraint violations on seeding
