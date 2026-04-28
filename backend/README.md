"""
Food Store Backend API

FastAPI-based REST API for the Food Store application.
Built with async/await, SQLModel ORM, and JWT authentication.

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 13+ (for database)
- pip or Poetry for dependency management

### Installation

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or with Poetry:
   ```bash
   poetry install
   poetry shell  # Activate poetry virtual environment
   ```

### Configuration

1. **Create `.env` file** from template
   ```bash
   cp .env.example .env
   ```

2. **Update `.env` with your configuration**
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/foodstore
   SECRET_KEY=your-secret-key-minimum-256-bits
   ENV=development
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

   **Important**: 
   - `SECRET_KEY` must be at least 256 bits (32 bytes) for security
   - Use different secrets for dev/test/prod environments
   - Never commit `.env` to version control

### Running the Development Server

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

**Options**:
- `--reload`: Auto-restart on file changes (development only)
- `--host 0.0.0.0`: Listen on all interfaces (useful for Docker)
- `--port 8001`: Use custom port
- `--log-level debug`: More verbose logging

### API Documentation

Once the server is running, visit:
- **Swagger UI** (interactive): http://localhost:8000/docs
- **ReDoc** (static): http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Health Check

Verify the API is running:
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core tests/

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

## Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── core/
│   ├── __init__.py
│   ├── config.py             # Environment configuration (Pydantic)
│   ├── database.py           # SQLAlchemy async engine & sessions
│   └── security.py           # JWT & password hashing utilities
├── tests/
│   ├── __init__.py
│   ├── test_config.py        # Config loading tests
│   └── test_security.py      # JWT & password tests
├── requirements.txt          # Python dependencies (lock file)
├── .env.example             # Environment template
└── .gitignore               # Git exclusions
```

Future sections (added in subsequent CHANGEs):
- `api/v1/` - API versioned routers (auth, products, orders, payments)
- `domain/` - Domain layer (entities, value objects, repositories, use cases)
- `infrastructure/` - Infrastructure layer (database models, DTOs, implementations)
- `migrations/` - Alembic database migrations

## Key Technologies

| Component | Technology | Version | Why |
|-----------|-----------|---------|-----|
| Framework | FastAPI | 0.109+ | Async-first, auto-validation, built-in OpenAPI docs |
| ORM | SQLModel | 0.0.14 | Combines SQLAlchemy & Pydantic, DRY schemas |
| Database | PostgreSQL | 13+ | Reliable, scalable, JSON support |
| Auth | JWT (HS256) | - | Stateless, scalable, standard |
| Hashing | Bcrypt | - | Slow (prevents brute force), automatic salting |
| Rate Limiting | slowapi | 0.1.9 | Token bucket algorithm, minimal overhead |
| Server | Uvicorn | 0.27+ | ASGI server, high performance |

## Architecture

This backend follows **DDD (Domain-Driven Design)** with **Onion Architecture**:

```
Presentation (API routes) → UseCase (business logic) → Infrastructure (DB) → Domain (pure logic)
```

**Key principle**: Dependencies always point inward. The Domain layer has zero external dependencies.

## Security

### JWT Tokens
- **Access tokens**: 30 minutes (short-lived, frequently rotated)
- **Refresh tokens**: 7 days (long-lived, rotated on use)
- **Algorithm**: HS256 (HMAC-SHA256) for development
- **Claims**: Follow RFC 7519 (iss, sub, aud, exp, iat, nbf, jti)

### Password Hashing
- **Algorithm**: Bcrypt
- **Cost**: 10 (configurable, ~100ms per hash)
- **Salt**: Automatic per password

### Error Responses
All errors follow **RFC 7807 Problem Details** format:
```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Validation Error",
  "detail": "Request validation failed",
  "status": 422,
  "instance": "/api/v1/users"
}
```

## Environment-Specific Configuration

### Development
- `ENV=development`
- SQL logging enabled
- CORS allows localhost
- Swagger docs available

### Test
- `ENV=test`
- In-memory database (NullPool)
- Minimal logging

### Production
- `ENV=production`
- SQL logging disabled
- CORS restricted to specified origins
- Error details hidden from responses

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "DATABASE_URL not found in environment"
```bash
# Create .env file with valid DATABASE_URL
cp .env.example .env
# Edit .env with your database connection string
```

### "Connection refused" on database startup
```bash
# Ensure PostgreSQL is running
# Check DATABASE_URL points to correct host/port
# Verify credentials
```

### Tests failing with "sqlalchemy.exc.ArgumentError"
Ensure `asyncpg` is installed:
```bash
pip install asyncpg
```

### CORS errors in browser
Verify `CORS_ORIGINS` in `.env` includes your frontend URL:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Next Steps

**CHANGE 3**: Database setup with Alembic migrations and seed data
**CHANGE 4**: Repository pattern and Unit of Work implementation
**CHANGE 5**: Authentication routes (login, register, token refresh)

## Contributing

Before committing changes:
1. Run tests: `pytest`
2. Check code style: `black --check .`
3. Type check: `mypy core/`
4. Follow DDD architecture patterns

## Questions or Issues?

See `openspec/changes/backend-setup/` for technical design decisions and specifications.
"""

# This is a module docstring, but we could also use it to run the app
if __name__ == "__main__":
    import uvicorn
    from core.config import settings
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_dev(),
    )
