# CHANGE 3: PostgreSQL Backend with Alembic Migrations and Seed Data

## Implementation Summary

This change implements a complete PostgreSQL database layer for FoodStore with:
- 15 SQLModel entities representing the domain
- Alembic migration framework for schema versioning
- Async SQLAlchemy ORM with psycopg driver
- Idempotent seed script for reference data

## Files Modified/Created

### Core Models (PHASE 2)
**File:** `backend/core/models.py`

Defined 15 SQLModel entities:
1. **Rol** — Role-based access control (ADMIN, STOCK, PEDIDOS, CLIENT)
2. **EstadoPedido** — Order lifecycle states
3. **FormaPago** — Payment methods
4. **Usuario** — User accounts with password hashing and soft delete
5. **RefreshToken** — JWT refresh token tracking
6. **DireccionEntrega** — Customer delivery addresses with soft delete
7. **Categoria** — Hierarchical product categories with soft delete
8. **Producto** — Store inventory with soft delete
9. **Ingrediente** — Product ingredients with allergen tracking
10. **ProductoCategoria** — N:M product-category pivot
11. **ProductoIngrediente** — N:M product-ingredient pivot with es_removible flag
12. **Pedido** — Customer orders with soft delete
13. **DetallePedido** — Order line items with price/ingredient snapshots
14. **HistorialEstadoPedido** — Append-only audit log (no soft delete)
15. **Pago** — Payment transactions with MercadoPago integration

### Database Configuration (PHASE 1)
**Files:** 
- `backend/core/database.py` — Updated to import all 15 models
- `backend/alembic.ini` — PostgreSQL async connection string
- `backend/alembic/env.py` — Async-compatible migration environment

### Migration (PHASE 3)
**File:** `backend/alembic/versions/001_initial_schema.py`

Manual migration creating all 15 tables with:
- Proper primary keys and composite keys for pivots
- Foreign key constraints with CASCADE/RESTRICT rules
- Naming conventions (FK_, PK_, IX_, UQ_)
- Indexes on frequently queried columns
- Soft delete pattern with `eliminado_en` timestamp
- Decimal fields for monetary values

### Seed Data (PHASE 5)
**File:** `backend/scripts/seed.py` (already existed, verified)

Idempotent seeding of:
- 4 roles (ADMIN, STOCK, PEDIDOS, CLIENT)
- 6 order states (PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO)
- 3 payment methods (MERCADOPAGO, EFECTIVO, TRANSFERENCIA)
- Admin user (admin@foodstore.com)

### Documentation
**Files:**
- `MIGRATION_STEPS.md` — Step-by-step execution guide
- `.env` — Updated with PostgreSQL connection string

## Architecture Decisions

### Soft Delete Pattern
Applied to mutable entities (Usuario, Producto, Pedido, etc.):
- `eliminado_en: Optional[datetime] = None`
- Filter queries with `WHERE eliminado_en IS NULL`
- Preserves audit trail while removing from active queries

### Foreign Key Cascade Rules
- **CASCADE:** Ownership relationships (user → tokens, addresses)
- **RESTRICT:** Audit/reference relationships (pedido → historial_estado_pedido)

### Pivot Tables
ProductoCategoria and ProductoIngrediente use:
- Composite primary keys (producto_id, categoria_id)
- CASCADE delete rules for automatic cleanup
- es_removible flag on ProductoIngrediente for customization

### Append-Only Audit
HistorialEstadoPedido has NO soft delete or update timestamp:
- Immutable log of state transitions
- Only creado_en for audit trail
- Used by order management FSM

### Async Support
- Uses psycopg (async) driver for PostgreSQL
- Windows-compatible event loop (SelectorEventLoop)
- Connection pooling for performance

## How to Use

### Prerequisites
- Docker and docker-compose running
- PostgreSQL container will start on 5432
- Credentials: postgres/postgres, database: foodstore_db

### Apply Migrations
```bash
cd backend
alembic upgrade head
```

### Seed Data
```bash
cd backend
python scripts/seed.py
```

### Verify
```bash
# Connect to database
docker exec -it foodstore-postgres psql -U postgres -d foodstore_db

# Check tables
\dt

# Verify data
SELECT COUNT(*) FROM roles;
SELECT * FROM usuarios WHERE eliminado_en IS NULL;
```

## Testing Strategy

### 1. Soft Delete Filtering
```sql
UPDATE usuarios SET eliminado_en = NOW() WHERE email = 'admin@foodstore.com';
SELECT * FROM usuarios WHERE eliminado_en IS NULL;  -- Should exclude deleted user
```

### 2. Foreign Key Constraints
```sql
-- Should fail: non-existent user
INSERT INTO pedidos (...) VALUES (999, ...);
```

### 3. Idempotency
```bash
python scripts/seed.py  # Run twice, should show [EXISTS] messages
```

### 4. Cascade Delete
```sql
DELETE FROM usuarios WHERE id = 1;  -- Should cascade to tokens, orders
```

## Key Design Patterns

### Domain-Driven Design
- Each table represents a domain aggregate
- Entities maintain invariants (price > 0, etc.)
- Value objects (Decimal, datetime)

### Unit of Work Pattern (prep for CHANGE 4)
- AsyncSession for transaction management
- `get_db_context()` function for UoW support
- Session factory for dependency injection

### Repository Pattern (prep for CHANGE 4)
- SQLAlchemy Select for query building
- Async/await for non-blocking operations

## Naming Conventions

### Models
- PascalCase: Usuario, Producto, Pedido
- Methods: snake_case: hash_password(), verify_password()

### Tables
- snake_case: usuarios, productos, pedidos
- Defined via `__tablename__` attribute

### Constraints
- Foreign keys: fk_{table}_{column}_{ref_table}
- Primary keys: pk_{table}
- Indexes: ix_{table}_{column}
- Unique: uq_{table}_{column}

## Performance Considerations

### Indexes
- usuario.email (unique, for login)
- producto.nombre (for search)
- producto.eliminado_en (for soft delete filtering)
- Similar indexes on mutable tables

### Connection Pooling
- Pool size: 20 (configurable)
- Max overflow: 10
- Pre-ping to verify connections

### Decimal Precision
- Monetary fields: `Decimal(precision=10, scale=2)`
- Handles up to 99,999.99

## Security Notes

- Passwords hashed with bcrypt (cost=10)
- MercadoPago integration tracks idempotency_key
- Foreign keys prevent orphaned records
- Audit trail via HistorialEstadoPedido

## Troubleshooting

### PostgreSQL Not Accessible
1. Check Docker: `docker ps`
2. Check logs: `docker-compose logs postgres`
3. Verify DATABASE_URL in `.env`

### Migration Fails
1. Check Python syntax: `python -m py_compile alembic/versions/001_initial_schema.py`
2. Verify models import: `python -c "from core.models import *"`
3. Check foreign key references

### Seed Script Errors
1. Run in backend directory: `cd backend`
2. Add backend to path: `export PYTHONPATH=.`
3. Check admin@foodstore.com doesn't exist

## Next Steps (CHANGE 4)

With this schema in place, CHANGE 4 will implement:
- Repository pattern for data access
- Use case layer for business logic
- Dependency injection with FastAPI
- Unit of Work for transactions
