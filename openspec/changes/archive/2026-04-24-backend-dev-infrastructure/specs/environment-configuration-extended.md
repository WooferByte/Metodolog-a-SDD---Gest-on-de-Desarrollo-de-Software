# Environment Configuration Extended

## Overview

Development, testing, and local work require configuration variables (database credentials, API keys, feature flags) that differ from production. This capability specifies a `.env.example` template and `.env` pattern to manage configuration safely.

## Functional Requirements

1. **`.env.example` File**:
   - Committed to git (NOT in `.gitignore`)
   - Template for developers: copy to `.env.local` and fill in values
   - All variables documented with descriptions and examples

2. **Database Configuration Variables**:
   - `DATABASE_URL`: Full connection string (used by CHANGE 2+ core)
   - `POSTGRES_USER`: Database user for docker-compose
   - `POSTGRES_PASSWORD` / `DB_PASSWORD`: User password
   - `POSTGRES_DB`: Database name for docker-compose

3. **Feature Flags**:
   - `SEED_DATABASE`: Boolean, controls whether to auto-seed on startup (optional)

4. **Security**:
   - Actual `.env` file MUST be in `.gitignore` (never committed)
   - Developers work with `.env.local` (or `.env`) loaded from `.env.example`
   - Production uses CI/CD secrets, not .env files

## Non-Functional Requirements

1. **Clarity**: Each variable documented with:
   - Description (what it controls)
   - Example value
   - Required/optional flag

2. **DRY**: No duplicate or conflicting variable names
   - Use single source of truth: `DATABASE_URL` for backend, not separate host/port/user vars

3. **Consistency**: Format follows Pydantic BaseSettings conventions
   - Variables in UPPERCASE with underscores
   - Types inferred from defaults or explicitly documented

4. **Tooling**:
   - Docker Compose can read `.env` automatically
   - Python Pydantic BaseSettings can parse `.env` with `python-dotenv`
   - No custom parsing required

## API / Interface

### File Structure

```
repository/
├── .env.example          # Committed to git (template)
├── .env                  # Not committed (.gitignore)
├── docker-compose.yml    # References ${VAR} from .env
└── backend/
    └── core/
        └── config.py     # Pydantic BaseSettings loads .env
```

### `.env.example` Template

```bash
# ============================================================================
# Database Configuration (Local Development)
# ============================================================================

# Full database connection string (psycopg driver, async)
# Format: postgresql+psycopg://user:password@host:port/database
# Docker example: postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db
# Native example: postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db
DATABASE_URL=postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db

# PostgreSQL Docker Compose Configuration
# Used by docker-compose.yml to initialize container
POSTGRES_USER=foodstore_user
POSTGRES_PASSWORD=foodstore_dev
POSTGRES_DB=foodstore_db
DB_PASSWORD=foodstore_dev

# ============================================================================
# Application Configuration
# ============================================================================

# FastAPI app title (displayed in Swagger UI)
APP_TITLE=Food Store API

# Environment: development, testing, production
ENVIRONMENT=development

# FastAPI debug mode (never use True in production)
DEBUG=True

# Secret key for JWT signing (generate: openssl rand -hex 32)
SECRET_KEY=your-secret-key-change-in-production

# ============================================================================
# Seed Database Configuration (Optional)
# ============================================================================

# Auto-seed database on app startup (True/False)
SEED_DATABASE=False

# ============================================================================
# Payment Integration (MercadoPago)
# ============================================================================

# MercadoPago API credentials (from https://www.mercadopago.com/settings/account/api)
MP_PUBLIC_KEY=your-public-key
MP_ACCESS_TOKEN=your-access-token

# ============================================================================
# CORS Configuration
# ============================================================================

# Frontend URL (for CORS allow origins)
FRONTEND_URL=http://localhost:5173

# ============================================================================
# Logging
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

### Python Usage (Pydantic BaseSettings)

```python
# backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg://..."
    
    # Application
    app_title: str = "Food Store API"
    environment: str = "development"
    debug: bool = False
    secret_key: str
    
    # Seed
    seed_database: bool = False
    
    # Payments
    mp_public_key: str
    mp_access_token: str
    
    # CORS
    frontend_url: str = "http://localhost:5173"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"  # Loaded by python-dotenv

settings = Settings()
```

### Docker Compose Usage

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-foodstore_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-foodstore_dev}
      POSTGRES_DB: ${POSTGRES_DB:-foodstore_db}
```

## Acceptance Criteria

- [ ] `.env.example` exists in repo root and is committed to git
- [ ] `.env.example` contains all variables: DATABASE_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, APP_TITLE, ENVIRONMENT, DEBUG, SECRET_KEY, etc.
- [ ] Each variable is documented with description and example value
- [ ] `.env` is in `.gitignore` (never committed)
- [ ] Docker Compose can read variables: `docker-compose config` shows interpolated values
- [ ] Pydantic BaseSettings loads `.env`: `from backend.core.config import settings` works
- [ ] Copying `.env.example` → `.env.local` and modifying values allows app to start
- [ ] No hardcoded credentials in code or config.py
- [ ] Production deployment documented: "Use CI/CD secrets, not .env files"
