## Context

Food Store backend is built on **FastAPI + SQLModel + PostgreSQL** following DDD/Onion Architecture patterns. This change establishes the foundational layer: application configuration, database abstraction, security utilities, and HTTP middleware. All subsequent changes (auth, products, orders, payments) depend on this infrastructure.

Current state: Only monorepo structure exists (CHANGE 1). No FastAPI code, no database connections, no config management.

## Goals / Non-Goals

**Goals:**
- Set up FastAPI application with production-ready middleware (CORS, rate limiting, error handling)
- Implement async SQLAlchemy session management and connection pooling
- Create centralized environment configuration (dev/test/prod modes)
- Provide JWT and password hashing utilities (used by auth, payments, admin)
- Enable OpenAPI documentation (Swagger, ReDoc)

**Non-Goals:**
- Implement any business logic routers (auth, products, etc.) — that's CHANGE 3+
- Create database migrations or schema (that's CHANGE 3: backend-postgres-alembic-seed)
- Implement repository patterns or Unit of Work (that's CHANGE 4: backend-patterns-base-repository-uow)

## Decisions

### 1. FastAPI over Django/Flask
**Choice**: FastAPI (async-first, auto-validation, built-in OpenAPI docs)
**Why**: 
- ASGI-based → handles async naturally (important for concurrent I/O like database queries, API calls)
- Pydantic integration → validation inline, no double-definition between models and schemas
- Auto-docs reduce maintenance burden
**Alternative rejected**: Django (heavier, built for sync, REST overhead)

### 2. SQLModel over raw SQLAlchemy + Pydantic
**Choice**: SQLModel (combines SQLAlchemy ORM with Pydantic validation)
**Why**: 
- Single model definition serves both database schema AND API schemas → DRY, type-safe
- Reduces boilerplate compared to SQLAlchemy + separate Pydantic schemas
- Full SQLAlchemy power (relationships, queries) under the hood
**Alternative rejected**: Pure SQLAlchemy (requires separate Pydantic schemas, more boilerplate)

### 3. Async Session Factory
**Choice**: Implement `async_session` factory using SQLAlchemy's `AsyncSession` + connection pooling
**Why**: 
- Non-blocking database I/O → can handle multiple concurrent requests
- Better resource utilization than thread-pool approach
- Aligns with FastAPI's async-first philosophy
**Alternative rejected**: Sync sessions (blocks event loop, limits concurrency)

### 4. Environment Configuration via Pydantic BaseSettings
**Choice**: `core/config.py` with Pydantic `BaseSettings` (auto-loads from `.env`)
**Why**: 
- Type-safe configuration (Pydantic validates all env vars at startup)
- Fail-fast if required env vars are missing
- Supports multiple environments (dev/test/prod) via `ENV` var
- Single source of truth for all config
**Alternative rejected**: os.getenv() scattered throughout code (no validation, hard to track requirements)

### 5. JWT with refresh token rotation
**Choice**: Access token (30 min) + Refresh token (7 days) with refresh-token rotation
**Why**: 
- Short access tokens limit damage if token is stolen
- Refresh tokens allow long sessions without re-entering password
- Rotation on refresh prevents replay attacks
- Complies with OWASP/PCI best practices
**Alternative rejected**: Single long-lived token (security risk), stateless-only (no revocation capability)

### 6. Bcrypt cost factor >= 10
**Choice**: Passlib with bcrypt cost=10 (or configurable via env)
**Why**: 
- Cost=10 takes ~100ms to hash (prevents brute force)
- Cost can increase over time as hardware improves
- Salts handled automatically
**Alternative rejected**: cost < 10 (too fast, vulnerable to brute force)

### 7. Rate limiting on sensitive endpoints
**Choice**: slowapi (token bucket algorithm) — 5 requests per 15 minutes on `/login`
**Why**: 
- Protects login endpoint from brute force attacks
- Minimal performance overhead
- Can be extended to other endpoints (payments, admin) later
**Alternative rejected**: No rate limiting (vulnerable)

### 8. RFC 7807 error responses
**Choice**: All errors returned as JSON with `type`, `title`, `detail`, `status` per RFC 7807
**Why**: 
- Standard error format → clients can parse predictably
- Includes enough info for debugging without exposing internals
- Professional/expected by API consumers
**Alternative rejected**: Unstructured error messages (hard to parse, inconsistent)

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| PostgreSQL connection exhaustion | Implement connection pooling with max_overflow limit, monitor in production |
| Async context issues (transactional scopes) | Use dependency injection (Depends) to scope sessions to request lifetime |
| JWT secret compromise | Store `SECRET_KEY` in `.env`, never in code; rotate on compromise |
| Database migrations out-of-sync with code | Alembic (CHANGE 3) will enforce strict versioning; only run migrations in deploy pipeline |
| Rate limiting bypass (proxies/load balancers) | Slowapi uses X-Forwarded-For; ensure load balancer strips untrusted headers in production |

**Trade-off**: Async session factory adds complexity (testing is slightly harder) vs. gain of non-blocking I/O (required for scalability).

## Migration Plan

1. **Create `backend/` directory structure** (if not exists from CHANGE 1)
   ```
   backend/
   ├── main.py              ← FastAPI app entry point
   ├── core/
   │   ├── config.py        ← Pydantic BaseSettings
   │   ├── database.py      ← SQLAlchemy engine + async_session
   │   └── security.py      ← JWT + bcrypt utilities
   ├── requirements.txt     ← Poetry dependencies
   └── .env.example         ← Template for env vars
   ```

2. **Install dependencies** via Poetry:
   ```bash
   cd backend
   poetry add fastapi uvicorn sqlmodel alembic passlib[bcrypt] python-jose slowapi httpx "pydantic[email-validator]" mercadopago
   ```

3. **Implement core modules** in order:
   - `config.py` first (no dependencies)
   - `database.py` (depends on config)
   - `security.py` (depends on config)
   - `main.py` (ties all together)

4. **Test locally**:
   ```bash
   cd backend
   poetry shell
   uvicorn main:app --reload
   ```
   Visit `http://localhost:8000/docs` → should see Swagger UI

5. **Rollback strategy**: No database changes yet, so simply revert `backend/` folder to previous commit.

## Open Questions

- [ ] Should we enable HTTPS/SSL for development? (defer to prod deployment)
- [ ] Should `main.py` initialize a database connection at startup? (defer until CHANGE 3 when DB exists)
- [ ] Should we add structured logging (JSON) from start? (defer unless performance profiling shows need)
