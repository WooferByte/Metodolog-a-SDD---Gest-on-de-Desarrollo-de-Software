## Why

CHANGE 2 (backend-fastapi-core-setup) establishes the FastAPI framework and core infrastructure, but left development and deployment infrastructure incomplete. Without Docker, fixed database driver compatibility, and seed data scripts, the backend is unusable in local development or CI/CD pipelines — developers cannot spin up a PostgreSQL instance easily, and Windows users face driver conflicts with `asyncpg/psycopg2-binary`.

This change closes the gap by providing:
1. **docker-compose.yml** for effortless local PostgreSQL setup
2. **psycopg[binary]** fix for Windows compatibility (replaces asyncpg/psycopg2-binary)
3. **scripts/seed.py** for idempotent test data injection (works both Docker + native PostgreSQL)
4. Updated **.env.example** to document all new configuration variables

This is a **blocker for CHANGE 3** (backend-postgres-alembic-seed) — without these, CHANGE 3 cannot assume a working development environment.

## What Changes

- **requirements.txt**: Replace `asyncpg==0.29.0` + `psycopg2-binary==2.9.9` with `psycopg[binary]==3.1.17` (works natively on Windows, Linux, macOS)
- **docker-compose.yml** (NEW): Spin up PostgreSQL 16 Alpine with health checks, volume persistence, automatic teardown
- **backend/scripts/seed.py** (NEW): Idempotent seed script that injects 4 Roles, 6 OrderStates, 3 PaymentMethods, 1 admin user (detects and skips if already exists)
- **.env.example**: Document `DATABASE_URL`, `SEED_DATABASE` (boolean), `POSTGRES_USER`, `POSTGRES_PASSWORD`
- **backend/.gitkeep** → **backend/scripts/.gitkeep** (establish scripts directory)
- **README.md** (update): Add "Getting Started" section with Docker instructions

## Capabilities

### New Capabilities

- `development-database-setup`: Docker-based PostgreSQL local development environment with health checks and data persistence
- `database-driver-compatibility`: Cross-platform database driver (Windows, Linux, macOS) using psycopg[binary] v3
- `seed-data-idempotent`: Idempotent seed script that initializes reference data without duplicates (Roles, OrderStates, PaymentMethods, admin user)
- `environment-configuration-extended`: Documentation and templates for development environment variables (DATABASE_URL, SEED_DATABASE, POSTGRES_*)

### Modified Capabilities

- `fastapi-app-core`: Update requirements.txt dependency from `asyncpg/psycopg2-binary` to `psycopg[binary]` (no behavior change, driver swap only)
- `database-sqlalchemy`: No spec change, but DATABASE_URL format will now use psycopg (e.g., `postgresql+psycopg://user:pass@localhost/db` instead of asyncpg URI)

## Impact

**Affected Code:**
- `backend/requirements.txt` — dependency update
- `backend/core/config.py` — may need to verify DATABASE_URL format compatibility (psycopg vs asyncpg)
- `backend/core/database.py` — no changes required (SQLAlchemy AsyncEngine handles psycopg transparently)

**Affected Workflows:**
- **Local development setup**: Before: `pip install -r requirements.txt` + manual PostgreSQL installation. After: `docker-compose up -d && poetry run python scripts/seed.py`
- **CI/CD**: Can now use `docker-compose` in GitHub Actions without shell-specific commands
- **Windows developers**: No more `psycopg2-binary` compile errors

**New Dependencies:**
- `docker` (already likely installed for team)
- `docker-compose` (included with Docker Desktop)

**Breaking Changes:** None. This is a pure **addition**; CHANGE 2 code is not modified, only enhanced.

**New Team Processes:**
- Developers must run `docker-compose up -d` before starting dev server (or connect to native PostgreSQL)
- `.env.local` will override `.env.example` (add to `.gitignore` if not already there)
