## Context

Food Store backend is built on FastAPI + SQLModel + PostgreSQL (CHANGE 2 established the core). Local development requires a database instance and seed data. Currently:
- No Docker setup → developers must install PostgreSQL manually
- `asyncpg` + `psycopg2-binary` → Windows driver conflicts
- No seed script → test data must be created manually or via SQL

This change adds the missing infrastructure layer.

## Goals / Non-Goals

**Goals:**
- Provide `docker-compose.yml` for one-command PostgreSQL setup with health checks
- Replace asyncpg/psycopg2-binary with psycopg[binary] for cross-platform compatibility
- Create idempotent seed script for reference data (Roles, OrderStates, PaymentMethods, admin user)
- Document all new environment variables in `.env.example`
- Enable CI/CD pipelines to use Docker without shell-specific workarounds

**Non-Goals:**
- Implement application-specific seed data (products, categories, etc.) — that's CHANGE 3+ (business domain changes)
- Set up Kubernetes or production-grade container orchestration
- Create database migrations (that's CHANGE 3: backend-postgres-alembic-seed)
- Change CHANGE 2 code or architecture

## Decisions

### 1. psycopg[binary] v3 over asyncpg

**Choice**: `psycopg[binary]==3.1.17` (latest stable)

**Why**:
- ✅ Works natively on Windows, Linux, macOS (no compile step)
- ✅ Full async support via `psycopg.AsyncConnection` (compatible with SQLAlchemy `AsyncEngine`)
- ✅ Modern, maintained, replaces psycopg2 (v2 is legacy)
- ✅ Single driver for all platforms (no need for both asyncpg + psycopg2-binary)

**Alternative rejected**: `asyncpg` (Python-only, incompatible with SQLAlchemy 2.0+ async without adapter)

### 2. Docker Compose (not Docker Swarm / Kubernetes)

**Choice**: `docker-compose.yml` (v3.8 format)

**Why**:
- ✅ Simple, single file, easy to version control
- ✅ Works with Docker Desktop (standard for local dev)
- ✅ CI/CD friendly (GitHub Actions supports it natively)
- ✅ No learning curve for team (industry standard)

**Alternative rejected**: Manual PostgreSQL installation (not portable across Windows/Linux/Mac)

### 3. PostgreSQL 16 Alpine in Docker

**Choice**: `image: postgres:16-alpine`

**Why**:
- ✅ Alpine = minimal image size (~50MB vs 200MB+ for full)
- ✅ PostgreSQL 16 = latest LTS, excellent async support
- ✅ Matches production likely version

**Configuration**:
```yaml
environment:
  POSTGRES_USER: foodstore_user
  POSTGRES_PASSWORD: ${DB_PASSWORD:-foodstore_dev}  # from .env
  POSTGRES_DB: foodstore_db
ports:
  - "5432:5432"
volumes:
  - postgres_data:/var/lib/postgresql/data  # persist across restarts
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U foodstore_user"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### 4. Idempotent Seed Script (Python, not SQL)

**Choice**: `backend/scripts/seed.py` (Python script, imported as module)

**Why**:
- ✅ Type-safe via SQLModel (vs raw SQL)
- ✅ Uses existing CHANGE 2 core (config, database, security)
- ✅ Easy to version alongside code
- ✅ Idempotent: checks if data exists before INSERT (no duplicates)
- ✅ Works with Docker or native PostgreSQL (only needs `DATABASE_URL`)

**Seed Data**:
```python
# Roles (4)
ADMIN, STOCK, PEDIDOS, CLIENT

# OrderStates (6)
PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO

# PaymentMethods (3)
MERCADOPAGO, EFECTIVO, TRANSFERENCIA

# Users (1)
admin@foodstore.com (password: Admin123!, role: ADMIN)
```

### 5. Environment Variable Strategy

**Choice**: `.env.example` (committed, template) + `.env` (local, in `.gitignore`)

**New Variables**:
```
DATABASE_URL=postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db
SEED_DATABASE=true  # auto-seed on app startup or manual via CLI?
POSTGRES_USER=foodstore_user
POSTGRES_PASSWORD=foodstore_dev
POSTGRES_DB=foodstore_db
```

**Why**:
- Template in git allows team to copy `.env.example → .env`
- Actual values in `.env` stay local (never committed)
- Docker compose can read from `.env` (docker-compose auto-loads it)

### 6. Health Check in Docker Compose

**Choice**: `healthcheck` with `pg_isready`

**Why**:
- Ensures PostgreSQL is ready before backend app starts
- Useful in CI/CD to wait for DB before running tests
- Prevents "connection refused" race conditions

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U foodstore_user"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Docker Desktop not installed on dev machine | Add fallback docs: "Use native PostgreSQL if Docker unavailable" |
| `.env` file accidentally committed | Add pre-commit hook to block `.env` commits (or mention in CONTRIBUTING.md) |
| seed.py run multiple times causes duplicates | Idempotent logic: `get_or_create()` pattern, UNIQUE constraints in schema |
| PostgreSQL data lost when `docker-compose down` | Document: use `docker-compose down` (keeps volumes), not `docker-compose down -v` (removes data) |
| Database URL format incompatible with asyncpg | psycopg URI format is `postgresql+psycopg://...`, SQLAlchemy handles it transparently |

**Trade-off**: Running seed script manually vs. auto-seed on app startup.
- Pro auto-seed: No extra CLI command
- Con auto-seed: Harder to debug, changes db on every app start
- **Decision**: Manual execution (`poetry run python scripts/seed.py`) after `docker-compose up -d` or in `conftest.py` for tests

## Migration Plan

1. **Update `backend/requirements.txt`**:
   - Remove: `asyncpg==0.29.0`, `psycopg2-binary==2.9.9`
   - Add: `psycopg[binary]==3.1.17`

2. **Create `docker-compose.yml`** (root of repo):
   ```yaml
   version: '3.8'
   services:
     postgres:
       image: postgres:16-alpine
       environment:
         POSTGRES_USER: ${POSTGRES_USER:-foodstore_user}
         POSTGRES_PASSWORD: ${DB_PASSWORD:-foodstore_dev}
         POSTGRES_DB: ${POSTGRES_DB:-foodstore_db}
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-foodstore_user}"]
         interval: 10s
         timeout: 5s
         retries: 5
   volumes:
     postgres_data:
   ```

3. **Create `backend/scripts/seed.py`**:
   ```python
   import asyncio
   from sqlmodel import Session
   from backend.core.database import engine, async_session
   from backend.core.config import settings
   from backend.models import Rol, EstadoPedido, FormaPago, Usuario

   async def seed_database():
       async with async_session() as session:
           # Get or create roles
           # Get or create order states
           # Get or create payment methods
           # Get or create admin user
           await session.commit()

   if __name__ == "__main__":
       asyncio.run(seed_database())
   ```

4. **Update `.env.example`**:
   ```
   # Database (Docker Compose or Native)
   DATABASE_URL=postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db
   POSTGRES_USER=foodstore_user
   POSTGRES_PASSWORD=foodstore_dev
   POSTGRES_DB=foodstore_db
   SEED_DATABASE=true
   ```

5. **Update `README.md`** — add "Getting Started" section:
   ```markdown
   ## Getting Started

   ### Option 1: Docker (Recommended)
   \`\`\`bash
   docker-compose up -d
   poetry run python backend/scripts/seed.py
   cd backend && poetry run uvicorn main:app --reload
   \`\`\`

   ### Option 2: Native PostgreSQL
   - Install PostgreSQL 16+ locally
   - Create database: `createdb foodstore_db`
   - Create user: `createuser foodstore_user`
   - Set password: `ALTER USER foodstore_user WITH PASSWORD 'foodstore_dev';`
   - Run seed: `poetry run python backend/scripts/seed.py`
   - Start app: `cd backend && poetry run uvicorn main:app --reload`
   ```

## Open Questions

- [ ] Should `seed.py` be invoked on `poetry run` or manual CLI? (Leaning: manual for safety)
- [ ] Should `.env.local` override `.env` in development? (Leaning: yes, add to `.gitignore`)
- [ ] Should seed data include sample products/categories or just reference data? (Leaning: reference only, products/categories in CHANGE 3)
- [ ] Should we add a Makefile target `make dev-setup` for one-command setup? (Optional, deferred)
