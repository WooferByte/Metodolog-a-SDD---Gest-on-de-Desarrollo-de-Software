## Overview

Implement DDD infrastructure layer patterns: BaseRepository generic for all entities, Unit of Work for transaction coordination, JWT-based authentication dependencies, and RFC 7807 error handling middleware.

## Architecture

```
Presentation Layer (FastAPI routes)
    ↓ (depends on)
UseCase Layer (Business logic)
    ↓ (depends on)
Infrastructure Layer (CHANGE 4)
    - BaseRepository[T]
    - UnitOfWork
    - Dependencies: get_current_user(), require_role()
    - Middleware: RFC 7807 errors
    ↓ (depends on)
Domain Layer (CHANGE 3 models)
    - SQLModel entities (Usuario, Producto, Pedido, etc.)
```

## Design Decisions

### 1. Generic BaseRepository[T]
- Single implementation handles all entities (Usuario, Producto, Pedido, etc.)
- Methods: `create()`, `get_by_id()`, `list_all()`, `update()`, `soft_delete()`, `hard_delete()`
- Soft-delete queries automatically exclude `eliminado_en IS NOT NULL`
- Generic type `T` ensures type safety for entity IDs and models

### 2. Unit of Work Pattern
- `UnitOfWork` is async context manager (`async with UnitOfWork(...) as uow:`)
- Exposes repositories as attributes: `uow.usuarios`, `uow.productos`, `uow.pedidos`, etc.
- Single session shared across all repositories (transaction boundary)
- Auto-commit on success, auto-rollback on exception
- Dependencies: `Depends(get_uow)` injects UoW into route handlers

### 3. Authentication Dependencies
- `get_current_user()` extracts Bearer token, validates JWT, returns Usuario entity
- Used: `@app.get("/api/v1/pedidos", dependencies=[Depends(get_current_user)])`
- Raises 401 if token missing/invalid/expired
- Raises 403 if user is soft-deleted (`eliminado_en IS NOT NULL`)

### 4. RBAC Factory
- `require_role(roles: list[str])` returns a dependency
- Used: `@app.post("/api/v1/categorias", dependencies=[Depends(require_role(["ADMIN", "STOCK"]))])`
- Validates current user has at least one required role
- Raises 403 if role not found in JWT or user lacks permission

### 5. RFC 7807 Error Middleware
- Global middleware catches all exceptions and formats as Problem+JSON
- Structure: `{ type, title, status, detail, instance }`
- Non-500 errors don't expose stack traces
- 500 errors logged server-side with full traceback
- All Pydantic validation errors include field-level details

## Implementation Strategy

### Phase 1: BaseRepository[T]
- Create `infrastructure/repositories/base_repository.py`
- Generic class `BaseRepository[T]` with async methods
- Constructor: `__init__(session: AsyncSession, model_class: type[T])`
- Methods use SQLAlchemy core + SQLModel type hints

### Phase 2: Unit of Work
- Create `infrastructure/uow.py`
- Class `UnitOfWork` with `async def __aenter__` / `async def __aexit__`
- Attributes: `self.usuarios`, `self.productos`, `self.pedidos`, etc. (lazy-loaded)
- Dependency: `async def get_uow(session: AsyncSession) -> UnitOfWork`

### Phase 3: Authentication Dependencies
- Create `infrastructure/dependencies.py`
- Function: `async def get_current_user(auth_header: str = Header(...)) -> Usuario`
- Extract token → verify JWT → query Usuario by ID → check soft-delete

### Phase 4: RBAC Factory
- Function: `def require_role(roles: list[str]) -> Callable`
- Returns async callable that extracts current_user, checks roles

### Phase 5: Error Middleware
- Create `infrastructure/error_middleware.py`
- Global exception handler in `main.py`: `@app.exception_handler(Exception)`
- Format and return RFC 7807 response

## Database Schema

No schema changes — uses existing 15 tables from CHANGE 3.

## API Contracts

**Authentication Dependency**
```python
# Usage in route handler
@app.get("/api/v1/perfil")
async def get_profile(current_user: Usuario = Depends(get_current_user)):
    return {"email": current_user.email, "nombre": current_user.nombre}
```

**RBAC Dependency**
```python
# Usage in route handler
@app.post("/api/v1/categorias")
async def create_category(
    data: CreateCategoryRequest,
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(require_role(["ADMIN", "STOCK"]))
):
    # Only ADMIN or STOCK can reach here
    pass
```

**Unit of Work in Service Layer**
```python
async def create_product_service(uow: UnitOfWork, product_data: CreateProductRequest):
    async with uow:
        existing = await uow.productos.get_by_id(product_data.nombre)
        if existing:
            raise ProductAlreadyExistsError()
        new_product = Producto(**product_data.dict())
        await uow.productos.create(new_product)
```

## Testing Strategy

- Unit tests for `BaseRepository` with mocked AsyncSession
- Integration tests for `UnitOfWork` with test database
- Tests for `get_current_user()` with valid/invalid tokens
- Tests for `require_role()` with various role combinations
- Tests for RFC 7807 error formatting with different HTTP status codes
