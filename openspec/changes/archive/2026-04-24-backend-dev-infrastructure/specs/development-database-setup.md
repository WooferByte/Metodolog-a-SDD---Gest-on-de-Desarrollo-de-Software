# Development Database Setup (PostgreSQL + Docker)

## Overview

Local development requires a PostgreSQL instance that:
1. Can be provisioned in one command (`docker-compose up -d`)
2. Persists data across restarts
3. Includes health checks to prevent race conditions
4. Works on Windows, Linux, and macOS without configuration

This capability provides a docker-compose.yml that satisfies all requirements.

## Functional Requirements

1. **Docker Compose Service**: PostgreSQL 16 Alpine container
   - Image: `postgres:16-alpine`
   - Environment: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` from .env
   - Port: 5432 (exposed to localhost)

2. **Data Persistence**: Named volume `postgres_data` survives `docker-compose down`
   - Volume mounted at `/var/lib/postgresql/data`
   - Persists across container restarts

3. **Health Check**: `pg_isready` command
   - Interval: 10 seconds
   - Timeout: 5 seconds
   - Retries: 5
   - Ensures PostgreSQL is ready before application connects

4. **Environment Variables**:
   - `POSTGRES_USER`: Database user (default: `foodstore_user`)
   - `POSTGRES_PASSWORD`: User password (from `DB_PASSWORD` in .env)
   - `POSTGRES_DB`: Database name (default: `foodstore_db`)

## Non-Functional Requirements

1. **Performance**: Container startup < 5 seconds, health check passes within 30 seconds
2. **Reliability**: No data loss on `docker-compose down` (keep volumes)
3. **Simplicity**: Single file (docker-compose.yml), one command to start
4. **Portability**: Works with Docker Desktop on Windows/macOS and Docker Engine on Linux

## API / Interface

### Command Line Interface

```bash
# Start PostgreSQL
docker-compose up -d

# Check status
docker-compose ps

# Stop (data persists)
docker-compose down

# Stop and remove data
docker-compose down -v

# Connect to PostgreSQL
docker exec -it <container-name> psql -U foodstore_user -d foodstore_db

# View logs
docker-compose logs postgres
```

### Configuration

```yaml
# docker-compose.yml
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

## Acceptance Criteria

- [ ] `docker-compose up -d` starts PostgreSQL without errors
- [ ] `docker-compose ps` shows `postgres` service with status `Up (healthy)`
- [ ] Health check passes: `docker exec <container> pg_isready -U foodstore_user` returns 0
- [ ] Can connect from host: `psql -h localhost -U foodstore_user -d foodstore_db` works
- [ ] Data persists: `docker-compose down` + `docker-compose up -d` retains data
- [ ] `docker-compose logs postgres` shows clean startup, no errors
