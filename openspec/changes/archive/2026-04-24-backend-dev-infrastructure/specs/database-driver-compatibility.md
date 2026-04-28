# Database Driver Compatibility (psycopg[binary])

## Overview

FastAPI + SQLAlchemy + PostgreSQL requires a database driver. Different drivers have different compatibility profiles:
- `asyncpg`: Python-only, fast but doesn't compile natively on Windows
- `psycopg2-binary`: C-based, works on Windows but deprecated (v2 EOL)
- `psycopg[binary]`: Modern C adapter with pre-built binary wheels for all platforms

This capability specifies the use of `psycopg[binary]` to ensure cross-platform compatibility.

## Functional Requirements

1. **Driver**: `psycopg[binary]==3.1.17` (or latest 3.x)
   - Provides async adapter via `psycopg.AsyncConnection`
   - Works with SQLAlchemy 2.0+ `AsyncEngine`

2. **Platforms Supported**:
   - Windows (x86_64, ARM64)
   - Linux (x86_64, ARM64, AARCH64)
   - macOS (x86_64, ARM64)
   - All via pre-built wheels (no compilation required)

3. **SQLAlchemy Integration**:
   - URI dialect: `postgresql+psycopg://`
   - Async connection pooling: `create_async_engine("postgresql+psycopg://...")`
   - Session factory: `AsyncSession(bind=engine)` with async context manager

4. **Connection Parameters**:
   - Format: `postgresql+psycopg://<user>:<password>@<host>:<port>/<db>`
   - From `.env` via `DATABASE_URL`
   - Example: `postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db`

## Non-Functional Requirements

1. **Installation**: `pip install -r requirements.txt` must succeed on all platforms without C compiler
2. **Performance**: Async connection pooling, max_overflow limits to prevent exhaustion
3. **Compatibility**: Works with FastAPI, SQLAlchemy 2.0+, SQLModel
4. **Testing**: Works in pytest with `AsyncSession` and fixtures

## API / Interface

### Python Code

```python
# backend/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool, QueuePool

# Create engine with psycopg driver
engine = create_async_engine(
    DATABASE_URL,  # e.g., postgresql+psycopg://...
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=QueuePool,
    connect_args={"timeout": 10},
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

### Configuration (.env)

```
DATABASE_URL=postgresql+psycopg://foodstore_user:foodstore_dev@localhost:5432/foodstore_db
```

## Acceptance Criteria

- [ ] `pip install -r requirements.txt` succeeds on Windows, Linux, macOS
- [ ] `poetry install` completes without C compiler requirement
- [ ] `import psycopg` and `from psycopg import AsyncConnection` work
- [ ] SQLAlchemy engine creation: `create_async_engine("postgresql+psycopg://...")` succeeds
- [ ] Connection pool: `await engine.connect()` establishes connection
- [ ] Async session: `async with AsyncSession(engine) as session:` works
- [ ] Query execution: `await session.exec(select(Tabla))` returns results
- [ ] No warnings or deprecation notices in import or runtime
