## 1. Update Requirements & Dependencies

- [x] 1.1 Update `backend/requirements.txt`: Remove `asyncpg==0.29.0` and `psycopg2-binary==2.9.9`, add `psycopg[binary]==3.1.17`
- [x] 1.2 Verify psycopg driver compatibility in `backend/core/database.py` with new DATABASE_URL format
- [x] 1.3 Test poetry lock: `poetry install` in backend directory to ensure clean dependency graph

## 2. Docker Infrastructure

- [x] 2.1 Create `docker-compose.yml` in repo root with PostgreSQL 16 Alpine service, environment variables, health check, volume persistence
- [x] 2.2 Verify docker-compose syntax: `docker-compose config` succeeds without errors
- [ ] 2.3 Test docker-compose locally: `docker-compose up -d` spins up PostgreSQL, health check passes (⚠️ Requires Docker daemon running)
- [ ] 2.4 Verify PostgreSQL is accessible: `docker exec <container> pg_isready` confirms connection (⚠️ Requires Docker daemon running)
- [ ] 2.5 Verify volume persistence: `docker-compose down` and `docker-compose up -d` retains data (⚠️ Requires Docker daemon running)
- [x] 2.6 Create cleanup script or document: `docker-compose down -v` to remove everything (optional, for doc)

## 3. Environment Configuration

- [x] 3.1 Update `.env.example` with DATABASE_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, SEED_DATABASE
- [x] 3.2 Verify `.env` is in `.gitignore` (if not already)
- [x] 3.3 Copy `.env.example` → `.env.local` locally and verify backend can read DATABASE_URL

## 4. Seed Script Implementation

- [x] 4.1 Create `backend/scripts/` directory structure (mkdir with __init__.py)
- [x] 4.2 Implement `backend/scripts/seed.py`:
  - [x] 4.2.1 Import SQLModel, asyncio, backend.core.config, backend.core.database
  - [x] 4.2.2 Create `seed_database()` async function
  - [x] 4.2.3 Implement idempotent seed for Rol: ADMIN, STOCK, PEDIDOS, CLIENT
  - [x] 4.2.4 Implement idempotent seed for EstadoPedido: PENDIENTE, CONFIRMADO, EN_PREPARACIÓN, EN_CAMINO, ENTREGADO, CANCELADO
  - [x] 4.2.5 Implement idempotent seed for FormaPago: MERCADOPAGO, EFECTIVO, TRANSFERENCIA
  - [x] 4.2.6 Implement idempotent seed for admin user: email=admin@foodstore.com, password hashed, role=ADMIN
  - [x] 4.2.7 Add `if __name__ == "__main__": asyncio.run(seed_database())` entry point
  - [x] 4.2.8 Add docstring explaining what script does and how to run
- [ ] 4.3 Test seed script manually: `poetry run python backend/scripts/seed.py` succeeds without errors (⚠️ Requires PostgreSQL running)
- [ ] 4.4 Verify seed is idempotent: run script twice, no duplicate errors (⚠️ Requires PostgreSQL running)
- [ ] 4.5 Verify seed data in database: query roles, order states, payment methods, admin user from PostgreSQL (⚠️ Requires PostgreSQL running)

## 5. Database Model Validation

- [x] 5.1 Verify `backend/core/database.py` correctly creates AsyncEngine with psycopg+asyncpg URI dialect
- [x] 5.2 Test connection: Import engine in Python REPL and verify `await engine.dispose()` works
- [x] 5.3 Verify Pydantic BaseSettings in `backend/core/config.py` correctly loads DATABASE_URL from `.env`

## 6. Documentation Updates

- [x] 6.1 Update `README.md` with "Getting Started" section: Docker option and native PostgreSQL option
- [x] 6.2 Add inline comments in `docker-compose.yml` explaining each service and configuration
- [x] 6.3 Add inline comments in `backend/scripts/seed.py` explaining idempotent logic
- [x] 6.4 Document troubleshooting: common issues (Docker not installed, port 5432 already in use, etc.)

## 7. Integration Verification

- [ ] 7.1 Full end-to-end test (⚠️ Requires Docker & PostgreSQL running):
  - [ ] 7.1.1 `docker-compose up -d` starts PostgreSQL
  - [ ] 7.1.2 `poetry run python backend/scripts/seed.py` initializes data
  - [ ] 7.1.3 `cd backend && poetry run uvicorn main:app --reload` starts backend
  - [ ] 7.1.4 Visit `http://localhost:8000/docs` and verify Swagger UI loads
  - [ ] 7.1.5 Verify no database connection errors in logs
- [ ] 7.2 Validate with native PostgreSQL (if available) (⚠️ Requires PostgreSQL installed):
  - [ ] 7.2.1 Create local PostgreSQL instance
  - [ ] 7.2.2 Update `.env.local` with native DATABASE_URL
  - [ ] 7.2.3 Run seed script against native DB
  - [ ] 7.2.4 Verify backend starts and connects successfully

## 8. Git & Commit

- [x] 8.1 Stage all changes: `git add backend/requirements.txt docker-compose.yml backend/scripts/ .env.example README.md`
- [x] 8.2 Review changes: `git diff --staged` to verify correctness
- [x] 8.3 Create commit with conventional message: `feat(infra): add Docker Compose, fix psycopg driver, implement idempotent seed script`
- [x] 8.4 Verify commit: `git log -1 --stat` shows all modified/added files
- [x] 8.5 Create checkpoint: Tag commit as `change-2.5-checkpoint` for safe rollback
