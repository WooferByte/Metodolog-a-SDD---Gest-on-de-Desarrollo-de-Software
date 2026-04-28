## 1. Environment & Configuration

- [x] 1.1 Create `.env.example` template with all required variables (DATABASE_URL, SECRET_KEY, ENV, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, MERCADOPAGO_API_KEY)
- [x] 1.2 Create `backend/core/config.py` with Pydantic BaseSettings (dev/test/prod modes, all env vars with validation)
- [x] 1.3 Verify config loads correctly (test that missing env vars raise ValidationError)

## 2. Database Layer

- [x] 2.1 Create `backend/core/database.py` with SQLAlchemy engine (async, connection pooling)
- [x] 2.2 Implement `get_db()` async session generator (FastAPI dependency)
- [x] 2.3 Implement `get_db_context()` for UoW pattern (prepares for CHANGE 4)
- [x] 2.4 Test database module in isolation (verify async session creation, connection pooling limits)

## 3. Security Utilities

- [x] 3.1 Create `backend/core/security.py` with JWT utilities:
  - `create_access_token(data, expires_delta)` → returns JWT access token (HS256)
  - `create_refresh_token()` → returns random refresh token UUID
  - `verify_token(token)` → validates JWT, returns payload or raises HTTPException(401)
- [x] 3.2 Implement password hashing: `hash_password(password)`, `verify_password(password, hash)` using Passlib bcrypt (cost=10)
- [x] 3.3 Test all security functions (token creation/validation, password hashing/verification)

## 4. FastAPI Application Setup

- [x] 4.1 Create `backend/main.py` with FastAPI() app instance
- [x] 4.2 Add CORS middleware (allow http://localhost:3000 for frontend in dev)
- [x] 4.3 Add rate limiting middleware (slowapi: 5 requests per 15 min on `/api/v1/auth/login`)
- [x] 4.4 Add RFC 7807 error middleware (catches all exceptions, returns standard error format)
- [x] 4.5 Add startup/shutdown events (check database connection on startup)
- [x] 4.6 Add `/health` endpoint (returns 200 OK, used for deployment checks)
- [x] 4.7 Register Swagger docs at `/docs` and ReDoc at `/redoc` (auto-generated)

## 5. Dependencies & Package Management

- [x] 5.1 Create `backend/pyproject.toml` (or use Poetry) with all production dependencies:
  - fastapi, uvicorn, sqlmodel, alembic
  - passlib[bcrypt], python-jose, slowapi
  - httpx, pydantic[email-validator]
  - mercadopago
- [x] 5.2 Create `backend/requirements.txt` (lock file for production)
- [x] 5.3 Test dependency installation: `poetry install` → no errors

## 6. Testing & Verification

- [x] 6.1 Create minimal test file `backend/tests/test_config.py` (verify config loads)
- [x] 6.2 Create `backend/tests/test_security.py` (test JWT and password hashing)
- [x] 6.3 Start development server: `uvicorn main:app --reload`
- [x] 6.4 Verify Swagger UI works: visit `http://localhost:8000/docs`
- [x] 6.5 Verify health check: `curl http://localhost:8000/health` → 200 OK
- [x] 6.6 Verify error handling: call nonexistent endpoint → RFC 7807 error response
- [x] 6.7 Create README section documenting startup steps

## 7. Git & Checkpoints

- [x] 7.1 Create `.gitignore` rules for backend (venv, __pycache__, .env, *.db)
- [x] 7.2 Stage all backend files
- [x] 7.3 Create git commit: "feat: setup FastAPI core with config, database, security"
