# Technical Design: PostgreSQL Database with Alembic Migrations and Seed Data

## Context

FoodStore's backend (CHANGE 2: backend-fastapi-core-setup) provides FastAPI and async SQLAlchemy infrastructure, but lacks a concrete database schema and migration framework. The backend is async-first; any database setup must respect async/await patterns and be compatible with FastAPI's lifespan events.

**Current State:**
- FastAPI application initialized with async engine support in `backend/core/config.py`
- No Alembic migrations yet
- No SQLModel entity definitions
- No seed data or reference tables

**Constraints:**
- Windows development environment (must support docker-compose for PostgreSQL)
- Async context required (psycopg with asyncpg driver, SQLAlchemy async dialect)
- Schema must enforce business rules: soft deletes, audit trails, order state FSM
- Must support multiple API users with role-based access (will be enforced in API layer later)

**Stakeholders:**
- Backend Team: needs schema definition + migration tooling
- QA: needs seed data for testing
- DevOps: needs reproducible database setup

## Goals / Non-Goals

**Goals:**
- Design 15-table normalized schema covering Auth, Products, Orders
- Establish Alembic as version control for schema; make migrations reversible
- Implement audit fields (`creado_en`, `actualizado_en`, `eliminado_en`) on all mutable entities
- Support soft-delete queries: automatic filtering of `eliminado_en IS NOT NULL` rows
- Capture product price/name snapshots in order details to prevent retroactive changes
- Create append-only `historial_estado_pedido` for immutable audit trail
- Provide idempotent seed script for reference data (roles, order states, payment methods)
- Ensure async compatibility with FastAPI's async session management

**Non-Goals:**
- Row-level security (GRANTED for future); API layer will enforce authorization
- Full-text search indexing (out of scope for v1)
- Time-series data for order analytics (planned for CHANGE X)
- Multi-tenant support (single FoodStore per deployment)
- Real-time WebSocket schema subscriptions

## Decisions

### Decision 1: Async Alembic Context

**Choice:** Implement Alembic's `Script.context` in `alembic/env.py` with async engine and `run_async_migrations()`.

**Rationale:**
- FastAPI is async-first; all database interactions must be awaitable
- psycopg async driver requires `asyncpg` URI dialect: `postgresql+asyncpg://...`
- Alembic's default synchronous context would block the event loop
- Async migrations allow schema changes in production without API downtime (future consideration)

**Alternatives Considered:**
1. Synchronous SQLAlchemy engine (❌ blocks async event loop; defeats FastAPI async purpose)
2. Alembic offline mode + manual SQL (❌ loses version control; error-prone)
3. Manual SQL scripts in `backend/scripts/migrations/` (❌ no rollback; hard to track state)

**Implementation:**
```python
# alembic/env.py
async def run_async_migrations() -> None:
    """Run migrations in 'online' mode."""
    config = context.config
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

asyncio.run(run_async_migrations())
```

---

### Decision 2: SQLModel ORM over Plain SQLAlchemy

**Choice:** Use SQLModel for entity definitions; provides Pydantic validation + SQLAlchemy ORM in one class.

**Rationale:**
- FastAPI already returns Pydantic models; SQLModel eliminates duplication
- Automatic validation on model assignment (e.g., `usuario.email` enforces string)
- Cleaner integration: `response_model=UsuarioRead` same model used for DB and API
- Full SQLAlchemy ORM power (relationships, lazy loading, session management)

**Alternatives Considered:**
1. Plain SQLAlchemy declarative_base (❌ requires separate Pydantic schemas for API)
2. Dataclasses + manual ORM mapping (❌ no validation; verbose)
3. Tortoise ORM (❌ less mature; fewer integrations with FastAPI)

**Example:**
```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    nombre: str
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: Optional[datetime] = None
```

---

### Decision 3: Soft Delete Pattern with Automatic Filtering

**Choice:** Add `eliminado_en: Optional[datetime]` field to all mutable entities. Use hybrid properties or query defaults to exclude soft-deleted rows.

**Rationale:**
- Compliance requirement: audit trail must be preserved even after "deletion"
- `eliminado_en = NULL` (active), `eliminado_en != NULL` (deleted)
- Prevents accidental data loss; admin can restore via `UPDATE ... SET eliminado_en = NULL`
- Query filters ensure soft-deleted rows never appear in normal queries unless explicitly requested

**Alternatives Considered:**
1. Hard delete only (❌ violates audit compliance)
2. Separate `deleted_rows` archive table (❌ manual; error-prone; expensive migrations)
3. Temporal tables (PostgreSQL 15+; ❌ overkill for v1; not universally available)

**Implementation:**
```python
# In query layer or hybrid property
class UsuarioRepository:
    @staticmethod
    async def list_active():
        return await session.execute(
            select(Usuario).where(Usuario.eliminado_en.is_(None))
        )
    
    @staticmethod
    async def soft_delete(usuario_id: int):
        usuario = await session.get(Usuario, usuario_id)
        usuario.eliminado_en = datetime.utcnow()
        await session.commit()
```

---

### Decision 4: Price/Name Snapshots in Order Details

**Choice:** Store `precio_snapshot` and `nombre_snapshot` in `detalle_pedido` table; never fetch from `producto` at read time.

**Rationale:**
- **Historical Accuracy:** Order shows what customer paid/received at time of order, not current product price
- **Audit Trail:** Price changes don't retroactively alter historical orders
- **Reconciliation:** Payment processing compares stored price; guards against accidental discrepancies
- **Analytics:** Revenue reports use stored prices, not recalculated values

**Alternatives Considered:**
1. Always read from `producto` table (❌ violates audit; breaks reconciliation if product changes)
2. Temporal tables storing product history (❌ complexity; not in v1 scope)
3. Immutable `ProductoVersion` snapshots (❌ extra table; slower queries)

**Implementation:**
```python
class DetallePedido(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id")
    producto_id: int = Field(foreign_key="producto.id")  # For reference only
    precio_snapshot: float  # What customer paid
    nombre_snapshot: str    # Product name at order time
    cantidad: int
    excluded_ingredients: str = Field(default="{}")  # JSON array of excluded ingredient IDs
```

---

### Decision 5: Append-Only Audit History

**Choice:** `historial_estado_pedido` is insert-only; no UPDATE or DELETE allowed. Enforce via application logic + trigger (future).

**Rationale:**
- **Immutable Record:** Regulatory audits require proof of state changes; no updates allowed
- **Tamper-Evident:** If record is deleted, audit log detects the gap
- **Simple:** No version conflicts; chronological ordering guaranteed by insertion order

**Alternatives Considered:**
1. Updatable `estado_pedido_history` (❌ allows tampering; audit-unfriendly)
2. Event sourcing with full snapshots (❌ complex; out of v1 scope)
3. Separate append log + soft delete (❌ complicated queries)

**Implementation:**
```python
class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", index=True)
    estado_pedido_id: int = Field(foreign_key="estado_pedido.id")
    cambio_por: str  # User email or system
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    razon: Optional[str] = None  # "Admin cancelled", etc.
    
    # No actualizado_en or eliminado_en; immutable
```

---

### Decision 6: 15 Tables in 3 Domains

**Choice:** Organize schema by bounded domain (Auth+Users, Products, Orders+Payments) instead of flat structure.

**Rationale:**
- **Conceptual Clarity:** Each domain has a clear responsibility
- **FK Constraints:** Prevent cross-domain corruption (e.g., no orphaned pedidos without usuario)
- **Future Scaling:** Easier to migrate domain to separate service if needed
- **Query Patterns:** Queries naturally separate by domain; fewer N+1 risks

**Domains:**
```
Auth + Users (4 tables)
├── usuario (PK: id, UK: email, FK: rol_id)
├── rol (PK: id, immutable enum)
├── refresh_token (PK: id, FK: usuario_id)
└── direccion_entrega (PK: id, FK: usuario_id)

Products + Catalog (5 tables)
├── categoria (PK: id, FK: padre_id self-reference)
├── producto (PK: id, FK: categoria_id)
├── ingrediente (PK: id)
├── producto_categoria (PK: (producto_id, categoria_id))
└── producto_ingrediente (PK: (producto_id, ingrediente_id))

Orders + Payments (6 tables)
├── estado_pedido (PK: id, immutable enum)
├── pedido (PK: id, FK: usuario_id, estado_pedido_id)
├── detalle_pedido (PK: id, FK: pedido_id, producto_id)
├── historial_estado_pedido (PK: id, FK: pedido_id, append-only)
├── forma_pago (PK: id, immutable enum)
└── pago (PK: id, FK: pedido_id, forma_pago_id)
```

---

### Decision 7: Idempotent Seed Script

**Choice:** `scripts/seed.py` uses "get or create" pattern; each reference entry checked before insert.

**Rationale:**
- **Safe Re-runs:** Running seed twice doesn't fail; no duplicate key errors
- **Development:** Devs can reset DB and re-seed without manual SQL
- **CI/CD:** Seed can run in deployments without complex idempotency logic
- **Reference Data Isolation:** Only immutable reference tables seeded; no user/order data

**Alternatives Considered:**
1. Truncate + insert (❌ destructive; wipes test data)
2. Conditional `INSERT ... ON CONFLICT DO NOTHING` (❌ database-specific; less portable)
3. Manual SQL scripts (❌ not version-controlled; no validation)

**Implementation:**
```python
# scripts/seed.py
async def seed_roles(session: AsyncSession):
    for rol_name in ["ADMIN", "STOCK", "PEDIDOS", "CLIENT"]:
        existing = await session.execute(
            select(Rol).where(Rol.nombre == rol_name)
        )
        if not existing.scalars().first():
            rol = Rol(nombre=rol_name, descripcion=f"Role {rol_name}")
            session.add(rol)
    await session.commit()
```

## Risks / Trade-offs

### Risk 1: Windows PostgreSQL Setup Complexity
**Problem:** Docker Desktop + WSL2 + PostgreSQL port conflicts common on Windows.
**Mitigation:** Provide `docker-compose.yml` with pre-configured PostgreSQL; document WSL2 setup in CONTRIBUTING.md. Use local postgres container instead of system-wide.
**Trade-off:** Adds Docker dependency; requires 4GB+ RAM for Docker Desktop.

### Risk 2: Psycopg[binary] Compatibility
**Problem:** `psycopg[binary]` compiled wheels don't always match Windows/Linux architecture.
**Mitigation:** Use `.bin` wheels from GitHub releases; pin version in `pyproject.toml`. Provide fallback: `psycopg[c]` with libpq system lib.
**Trade-off:** Adds build complexity; requires manual testing on Windows + Linux CI.

### Risk 3: Async Session Lifecycle
**Problem:** FastAPI lifespan events must properly open/close async sessions; connection pool exhaustion if not managed.
**Mitigation:** Use dependency injection (FastAPI `Depends`); centralize session creation in `backend/core/db.py`. Document session scope rules in architecture guide.
**Trade-off:** Adds boilerplate; requires discipline on session cleanup.

### Risk 4: Migration Conflicts in Team
**Problem:** Two devs creating migrations simultaneously results in duplicate revision numbers.
**Mitigation:** Use Alembic branch/merge capabilities; establish naming convention: `YYYYMMDD_hhmm_description`. Code review all migrations before merge.
**Trade-off:** Adds coordination overhead; slower migration review cycle.

### Risk 5: Soft Delete Query Overhead
**Problem:** Every query must include `WHERE eliminado_en IS NULL`; can miss soft-deleted rows if filter forgotten.
**Mitigation:** Create repository base class with soft-delete filter applied by default. Add linter rule to catch raw `.select(Usuario)` without explicit soft-delete handling.
**Trade-off:** Slight query overhead; hidden complexity in query generation.

## Migration Plan

### Deploy Strategy (Future)
1. **Pre-deployment:** Run Alembic migration in staging environment first
2. **Schema Change:** `alembic upgrade head` (zero-downtime if using online migrations)
3. **Post-deploy:** Run seed script to ensure reference data present
4. **Verification:** Health check validates table structure + audit fields

### Rollback Strategy (If Needed)
```bash
# Rollback to specific revision
alembic downgrade ae1027a6acf

# Or downgrade by N steps
alembic downgrade -1
```

**Trade-off:** Downgrade reliability depends on well-written migration SQL; test rollbacks in staging first.

---

## Data Model Overview

### Table Structure (Audit Fields Pattern)
All mutable entities follow this pattern:
```sql
CREATE TABLE <entity> (
    id SERIAL PRIMARY KEY,
    -- business columns --
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW(),
    eliminado_en TIMESTAMP NULL,  -- soft delete marker
);

CREATE INDEX idx_<entity>_eliminado_en ON <entity>(eliminado_en);
```

### Cascade Rules
- `usuario` → `refresh_token`: CASCADE DELETE (if user deleted, tokens gone)
- `usuario` → `direccion_entrega`: CASCADE DELETE (if user deleted, addresses gone)
- `pedido` → `detalle_pedido`: CASCADE DELETE (if order deleted, line items gone)
- `pedido` → `historial_estado_pedido`: CASCADE DELETE (if order deleted, history gone)
- `producto` → nothing; `detalle_pedido.producto_id` nullable for deleted products (preserves historical orders)

### Unique Constraints
- `usuario.email` — UNIQUE (case-insensitive index if PostgreSQL supports)
- `producto.sku` — UNIQUE (business identifier)
- `categoria.nombre` — UNIQUE per parent (no duplicate category names under same parent)

---

## Implementation Notes

### Why Async Context in Alembic?
FastAPI runs on async event loop. If Alembic uses synchronous engine, `alembic upgrade` call blocks the loop. For production deployments with live traffic, this causes request timeouts. Async Alembic context allows schema changes without stopping the API.

### Why Price Snapshots?
Without snapshots, a product price change would silently alter all historical orders' revenues. For example:
- Order placed: Producto.precio = $10.00
- Later, product price updated to $8.00
- Revenue report queries `SELECT SUM(cantidad * producto.precio)` → undercounts revenue

With snapshots:
- `detalle_pedido.precio_snapshot = 10.00` (immutable)
- Revenue calculation always correct: `SELECT SUM(cantidad * precio_snapshot)`

### Why Append-Only History?
Regulatory audits (e.g., financial audits for payment disputes) require proof of order state changes. If history is updatable, an attacker could delete evidence. Append-only design makes tampering detectable: if expected state-change entries are missing, the gap is obvious.

---

## Open Questions

1. **Multi-language support:** Should `rol.nombre` and `estado_pedido.nombre` support i18n? (Tentative: defer to CHANGE X; store in Spanish for now)
2. **Soft delete UI:** Should deleted products appear in admin product list with a "deleted" badge? (Tentative: yes, but filtered by default)
3. **Audit log retention:** How long keep `eliminado_en` rows before hard-delete archival? (Tentative: 90 days; implement in separate CHANGE)
4. **Timezone handling:** Store timestamps in UTC; convert on API response? (Tentative: yes; document in API response schema)
5. **Seed data scope:** Should admin user have a password, or OAuth-only login? (Tentative: seed with temp password; require reset on first login; implement in CHANGE 4)
