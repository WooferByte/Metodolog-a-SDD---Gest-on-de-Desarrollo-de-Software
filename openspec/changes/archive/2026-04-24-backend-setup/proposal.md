## Why

The Food Store backend needs core infrastructure to operate: FastAPI framework, database abstraction layer, environment configuration, and HTTP middleware. Without this foundation, no business logic (auth, products, orders, payments) can be implemented. This change establishes the skeleton all subsequent changes depend on.

## What Changes

- **Initialize FastAPI application** with CORS middleware, rate limiting, and global error handling (RFC 7807)
- **Configure environment management** with `core/config.py` — centralized reading of DB, secrets, and app settings from `.env`
- **Set up database layer** with SQLAlchemy engine, session factory, and connection pooling via `core/database.py`
- **Implement security utilities** in `core/security.py` — JWT generation/validation, password hashing with bcrypt
- **Install all production dependencies** — FastAPI, SQLModel, Alembic, Passlib, python-jose, slowapi, MercadoPago SDK, httpx, Pydantic with email validator
- **Expose API documentation** — Swagger UI at `/docs`, ReDoc at `/redoc`
- **Enable Uvicorn as ASGI server** with hot-reload during development

No breaking changes (new system, no prior API exists).

## Capabilities

### New Capabilities

- `fastapi-app-core`: Core FastAPI application with CORS, rate limiting, error middleware
- `environment-configuration`: Centralized config from `.env` using Pydantic settings (development, test, production modes)
- `database-sqlalchemy`: SQLAlchemy engine, async session factory, connection pooling for PostgreSQL
- `security-jwt-hashing`: JWT token generation/validation (HS256), bcrypt password hashing with cost >= 10
- `api-documentation`: Auto-generated OpenAPI docs (Swagger/ReDoc)

### Modified Capabilities

None (first backend implementation).

## Impact

- **Code**: Creates `/backend/main.py`, `/backend/core/` module (config.py, database.py, security.py)
- **Dependencies**: Adds FastAPI, SQLModel, Alembic, python-jose, Passlib, slowapi, httpx, pydantic[email-validator], MercadoPago SDK
- **Environment**: Requires `.env` file (template provided in `.env.example`)
- **Database**: Prepares connection string configuration (actual DB setup is CHANGE 3)
- **API**: Opens port 8000 for development, enables documentation at `/docs`
