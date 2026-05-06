# Implementation Tasks: PostgreSQL Database with Alembic Migrations and Seed Data

## 1. Alembic Setup

- [x] 1.1 Initialize Alembic project: `alembic init alembic`
- [x] 1.2 Configure `alembic.ini` with PostgreSQL async connection string
- [x] 1.3 Update `alembic/env.py` to use async context manager (`asyncio.run()`)
- [x] 1.4 Update `alembic/env.py` to reference SQLModel metadata: `target_metadata = SQLModel.metadata`
- [x] 1.5 Add naming conventions to `alembic/env.py` for consistent FK/PK/IX naming

## 2. SQLModel Entities – Domain Auth + Users

- [x] 2.1 Create `backend/core/models.py` (or `backend/models/__init__.py`)
- [x] 2.2 Define `Rol` model (immutable enum: ADMIN, STOCK, PEDIDOS, CLIENT)
- [x] 2.3 Define `Usuario` model with email uniqueness, password hashing, soft delete
- [x] 2.4 Define `RefreshToken` model with token_hash, revoke tracking, expiration
- [x] 2.5 Define `DireccionEntrega` model with user FK, address fields, soft delete

## 3. SQLModel Entities – Domain Products + Catalog

- [x] 2.6 Define `Categoria` model with hierarchical self-reference (padre_id)
- [x] 2.7 Define `Producto` model with price, stock, availability, soft delete, categoria FK
- [x] 2.8 Define `Ingrediente` model with allergen flag
- [x] 2.9 Define `ProductoCategoria` pivot (N:M) with composite PK
- [x] 2.10 Define `ProductoIngrediente` pivot (N:M) with `es_removible` flag and composite PK

## 4. SQLModel Entities – Domain Orders + Payments

- [x] 2.11 Define `EstadoPedido` model (immutable enum: 6 states)
- [x] 2.12 Define `FormaPago` model (immutable enum: EFECTIVO, MERCADOPAGO, TARJETA)
- [x] 2.13 Define `Pedido` model with FSM state, totals, address FK, soft delete
- [x] 2.14 Define `DetallePedido` model with price snapshots, excluded_ingredients JSON
- [x] 2.15 Define `HistorialEstadoPedido` model (append-only; no actualizado_en or eliminado_en)
- [x] 2.16 Define `Pago` model with MercadoPago tracking, idempotency_key, gateway response JSON

## 5. Audit Fields on All Mutable Entities

- [x] 2.17 Add `creado_en: datetime = Field(default_factory=datetime.utcnow)` to: Usuario, DireccionEntrega, Categoria, Producto, Pedido, DetallePedido, RefreshToken, Pago
- [x] 2.18 Add `actualizado_en: datetime = Field(default_factory=datetime.utcnow)` to same entities
- [x] 2.19 Add `eliminado_en: Optional[datetime] = None` to: Usuario, DireccionEntrega, Categoria, Producto, Pedido
- [x] 2.20 Verify HistorialEstadoPedido has ONLY `creado_en` (no actualizado_en or eliminado_en)

## 6. Alembic Migration Generation

- [x] 3.1 Run `alembic revision --autogenerate -m "Initial schema creation with 15 tables"`
- [x] 3.2 Review generated migration file for correctness (check CASCADE rules, naming conventions)
- [x] 3.3 Manually fix any issues: verify all FKs use correct naming pattern, verify all indexes created
- [x] 3.4 Ensure migration is async-compatible (uses `async def` if needed)

## 7. Migration Application & Schema Verification

- [x] 4.1 Start PostgreSQL (via `docker-compose up -d` or local postgres service)
- [x] 4.2 Run migration: `alembic upgrade head`
- [x] 4.3 Verify all 15 tables created: `psql -U foodstore_user -d foodstore -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"`
- [x] 4.4 Verify `alembic_version` table exists and contains migration hash
- [x] 4.5 Verify indexes created for: usuario.email, producto.sku, producto.eliminado_en, etc.
- [x] 4.6 Verify ForeignKey constraints enforced: run `SELECT * FROM information_schema.referential_constraints`

## 8. Seed Data Script

- [x] 4.7 Create `backend/scripts/seed.py`
- [x] 4.8 Implement async SQLAlchemy session management in seed script
- [x] 4.9 Implement get_or_create pattern for immutable reference data
- [x] 4.10 Seed roles: create_if_not_exists(Rol.nombre = "ADMIN", "STOCK", "PEDIDOS", "CLIENT")
- [x] 4.11 Seed order states: create_if_not_exists(EstadoPedido.nombre = "PENDIENTE", "CONFIRMADO", "PREPARANDO", "LISTO", "ENTREGADO", "CANCELADO")
- [x] 4.12 Seed payment methods: create_if_not_exists(FormaPago.nombre = "EFECTIVO", "MERCADOPAGO", "TARJETA")
- [x] 4.13 Create admin user with temp password (seed with email: `admin@foodstore.local`, password hashed)

## 9. Testing & Validation

- [x] 4.14 Run seed script: `python backend/scripts/seed.py`
- [x] 4.15 Verify seed data created: `SELECT * FROM rol` (should have 4 rows)
- [x] 4.16 Verify soft-delete filtering: `SELECT * FROM usuario WHERE eliminado_en IS NULL` (should have admin user)
- [x] 4.17 Test soft delete: UPDATE usuario SET eliminado_en = NOW() WHERE id = ?; query should exclude this user
- [x] 4.18 Verify audit fields: check creado_en, actualizado_en timestamps on seeded records
- [x] 4.19 Verify relationships: test FK constraints (try inserting producto with non-existent categoria_id; should fail)
- [x] 4.20 Verify unique constraints: try inserting duplicate usuario.email; should fail
- [x] 4.21 Run seed script again (idempotency test): should complete without errors (no duplicates)

## 10. Documentation & Integration

- [x] 4.22 Update `backend/core/db.py` to initialize SQLModel.metadata and async engine
- [x] 4.23 Create `docker-compose.yml` with PostgreSQL service for development
- [x] 4.24 Document database setup in `CONTRIBUTING.md`: steps to start DB, run migrations, seed
- [x] 4.25 Add migration instructions to project README
- [x] 4.26 Verify FastAPI app can initialize with database connection (no errors on startup)
