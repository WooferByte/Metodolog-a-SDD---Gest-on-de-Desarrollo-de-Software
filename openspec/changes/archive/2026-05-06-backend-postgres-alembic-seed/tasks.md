# Implementation Tasks: PostgreSQL Database with Alembic Migrations and Seed Data

## 1. Alembic Setup

- [ ] 1.1 Initialize Alembic project: `alembic init alembic`
- [ ] 1.2 Configure `alembic.ini` with PostgreSQL async connection string
- [ ] 1.3 Update `alembic/env.py` to use async context manager (`asyncio.run()`)
- [ ] 1.4 Update `alembic/env.py` to reference SQLModel metadata: `target_metadata = SQLModel.metadata`
- [ ] 1.5 Add naming conventions to `alembic/env.py` for consistent FK/PK/IX naming

## 2. SQLModel Entities – Domain Auth + Users

- [ ] 2.1 Create `backend/core/models.py` (or `backend/models/__init__.py`)
- [ ] 2.2 Define `Rol` model (immutable enum: ADMIN, STOCK, PEDIDOS, CLIENT)
- [ ] 2.3 Define `Usuario` model with email uniqueness, password hashing, soft delete
- [ ] 2.4 Define `RefreshToken` model with token_hash, revoke tracking, expiration
- [ ] 2.5 Define `DireccionEntrega` model with user FK, address fields, soft delete

## 3. SQLModel Entities – Domain Products + Catalog

- [ ] 2.6 Define `Categoria` model with hierarchical self-reference (padre_id)
- [ ] 2.7 Define `Producto` model with price, stock, availability, soft delete, categoria FK
- [ ] 2.8 Define `Ingrediente` model with allergen flag
- [ ] 2.9 Define `ProductoCategoria` pivot (N:M) with composite PK
- [ ] 2.10 Define `ProductoIngrediente` pivot (N:M) with `es_removible` flag and composite PK

## 4. SQLModel Entities – Domain Orders + Payments

- [ ] 2.11 Define `EstadoPedido` model (immutable enum: 6 states)
- [ ] 2.12 Define `FormaPago` model (immutable enum: EFECTIVO, MERCADOPAGO, TARJETA)
- [ ] 2.13 Define `Pedido` model with FSM state, totals, address FK, soft delete
- [ ] 2.14 Define `DetallePedido` model with price snapshots, excluded_ingredients JSON
- [ ] 2.15 Define `HistorialEstadoPedido` model (append-only; no actualizado_en or eliminado_en)
- [ ] 2.16 Define `Pago` model with MercadoPago tracking, idempotency_key, gateway response JSON

## 5. Audit Fields on All Mutable Entities

- [ ] 2.17 Add `creado_en: datetime = Field(default_factory=datetime.utcnow)` to: Usuario, DireccionEntrega, Categoria, Producto, Pedido, DetallePedido, RefreshToken, Pago
- [ ] 2.18 Add `actualizado_en: datetime = Field(default_factory=datetime.utcnow)` to same entities
- [ ] 2.19 Add `eliminado_en: Optional[datetime] = None` to: Usuario, DireccionEntrega, Categoria, Producto, Pedido
- [ ] 2.20 Verify HistorialEstadoPedido has ONLY `creado_en` (no actualizado_en or eliminado_en)

## 6. Alembic Migration Generation

- [ ] 3.1 Run `alembic revision --autogenerate -m "Initial schema creation with 15 tables"`
- [ ] 3.2 Review generated migration file for correctness (check CASCADE rules, naming conventions)
- [ ] 3.3 Manually fix any issues: verify all FKs use correct naming pattern, verify all indexes created
- [ ] 3.4 Ensure migration is async-compatible (uses `async def` if needed)

## 7. Migration Application & Schema Verification

- [ ] 4.1 Start PostgreSQL (via `docker-compose up -d` or local postgres service)
- [ ] 4.2 Run migration: `alembic upgrade head`
- [ ] 4.3 Verify all 15 tables created: `psql -U foodstore_user -d foodstore -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"`
- [ ] 4.4 Verify `alembic_version` table exists and contains migration hash
- [ ] 4.5 Verify indexes created for: usuario.email, producto.sku, producto.eliminado_en, etc.
- [ ] 4.6 Verify ForeignKey constraints enforced: run `SELECT * FROM information_schema.referential_constraints`

## 8. Seed Data Script

- [ ] 4.7 Create `backend/scripts/seed.py`
- [ ] 4.8 Implement async SQLAlchemy session management in seed script
- [ ] 4.9 Implement get_or_create pattern for immutable reference data
- [ ] 4.10 Seed roles: create_if_not_exists(Rol.nombre = "ADMIN", "STOCK", "PEDIDOS", "CLIENT")
- [ ] 4.11 Seed order states: create_if_not_exists(EstadoPedido.nombre = "PENDIENTE", "CONFIRMADO", "PREPARANDO", "LISTO", "ENTREGADO", "CANCELADO")
- [ ] 4.12 Seed payment methods: create_if_not_exists(FormaPago.nombre = "EFECTIVO", "MERCADOPAGO", "TARJETA")
- [ ] 4.13 Create admin user with temp password (seed with email: `admin@foodstore.local`, password hashed)

## 9. Testing & Validation

- [ ] 4.14 Run seed script: `python backend/scripts/seed.py`
- [ ] 4.15 Verify seed data created: `SELECT * FROM rol` (should have 4 rows)
- [ ] 4.16 Verify soft-delete filtering: `SELECT * FROM usuario WHERE eliminado_en IS NULL` (should have admin user)
- [ ] 4.17 Test soft delete: UPDATE usuario SET eliminado_en = NOW() WHERE id = ?; query should exclude this user
- [ ] 4.18 Verify audit fields: check creado_en, actualizado_en timestamps on seeded records
- [ ] 4.19 Verify relationships: test FK constraints (try inserting producto with non-existent categoria_id; should fail)
- [ ] 4.20 Verify unique constraints: try inserting duplicate usuario.email; should fail
- [ ] 4.21 Run seed script again (idempotency test): should complete without errors (no duplicates)

## 10. Documentation & Integration

- [ ] 4.22 Update `backend/core/db.py` to initialize SQLModel.metadata and async engine
- [ ] 4.23 Create `docker-compose.yml` with PostgreSQL service for development
- [ ] 4.24 Document database setup in `CONTRIBUTING.md`: steps to start DB, run migrations, seed
- [ ] 4.25 Add migration instructions to project README
- [ ] 4.26 Verify FastAPI app can initialize with database connection (no errors on startup)
