# Infrastructure Layer Patterns - FoodStore Backend

This document describes the DDD infrastructure patterns implemented in CHANGE 4 (backend-patterns-base-repository-uow).

## Table of Contents

1. [BaseRepository[T] - Generic Repository Pattern](#baserepository-generic-repository-pattern)
2. [Unit of Work - Transaction Coordination](#unit-of-work-transaction-coordination)
3. [Authentication Dependencies](#authentication-dependencies)
4. [RBAC Factory - Role-Based Access Control](#rbac-factory-role-based-access-control)
5. [RFC 7807 Error Middleware](#rfc-7807-error-middleware)
6. [Integration Patterns](#integration-patterns)

---

## BaseRepository[T] - Generic Repository Pattern

### Overview

`BaseRepository[T]` is a generic, type-safe repository pattern that implements CRUD operations for all SQLModel entities. It provides automatic soft-delete filtering and support for complex queries.

### Location

```
backend/infrastructure/repositories/base_repository.py
```

### API

#### Constructor

```python
repo = BaseRepository[Usuario](session, Usuario)
```

#### Methods

| Method | Signature | Returns | Notes |
|--------|-----------|---------|-------|
| `create()` | `async def create(entity: T) -> T` | Entity with ID | Flushes to get ID |
| `get_by_id()` | `async def get_by_id(id: int) -> Optional[T]` | Entity or None | Filters soft-deleted |
| `list_all()` | `async def list_all(skip: int = 0, limit: int = 100) -> list[T]` | List of entities | Pagination support |
| `count()` | `async def count() -> int` | Count of active records | Filters soft-deleted |
| `update()` | `async def update(entity: T) -> T` | Updated entity | Sets `actualizado_en` |
| `soft_delete()` | `async def soft_delete(id: int) -> None` | None | Sets `eliminado_en` |
| `hard_delete()` | `async def hard_delete(id: int) -> None` | None | Permanent DELETE |
| `execute_query()` | `async def execute_query(query: Select) -> list[T]` | Query results | Raw SQLAlchemy |
| `execute_scalar()` | `async def execute_scalar(query: Select) -> Any` | Scalar result | For COUNT, etc. |

### Usage Examples

#### Create

```python
# Create a new product
product = Producto(
    nombre="Pizza Margarita",
    descripcion="Classic pizza",
    precio_base=Decimal("25.00"),
    stock_cantidad=100,
)
await repo.productos.create(product)
print(product.id)  # ID is now populated
```

#### Read

```python
# Get by ID (excludes soft-deleted)
product = await repo.productos.get_by_id(1)

# List with pagination
products = await repo.productos.list_all(skip=0, limit=50)

# Count active records
count = await repo.productos.count()
```

#### Update

```python
# Update an entity
product.stock_cantidad = 50
await repo.productos.update(product)
# Note: actualizado_en is automatically set to NOW()
```

#### Delete

```python
# Soft delete (mark as deleted, not removed from DB)
await repo.productos.soft_delete(1)

# Hard delete (permanent removal - use sparingly!)
await repo.productos.hard_delete(1)
```

#### Complex Queries

```python
from sqlalchemy import select, func

# Query products by name pattern
query = select(Producto).where(
    Producto.nombre.like("%Pizza%")
).where(
    Producto.disponible == True
)
pizzas = await repo.productos.execute_query(query)

# Count with WHERE clause
query = select(func.count(Producto.id)).where(
    Producto.stock_cantidad > 0
)
in_stock_count = await repo.productos.execute_scalar(query)
```

### Soft-Delete Behavior

**All** list/count/get_by_id queries automatically exclude soft-deleted records (where `eliminado_en IS NOT NULL`). This is transparent and happens without explicit WHERE clauses in your code.

**Exception:** Use `execute_query()` to bypass soft-delete filtering when needed for admin/compliance operations.

---

## Unit of Work - Transaction Coordination

### Overview

`UnitOfWork` is an async context manager that coordinates multiple repositories within a single database transaction. It ensures atomicity: all changes commit together or all rollback on exception.

### Location

```
backend/infrastructure/uow.py
```

### API

```python
async with UnitOfWork(session) as uow:
    # All repository operations share the same transaction
    user = await uow.usuarios.create(new_user)
    order = await uow.pedidos.create(new_order)
    # Auto-commits on successful exit
    # Auto-rolls back if exception occurs
```

### Repository Attributes

All 14 entities have corresponding repository attributes:

```python
uow.usuarios              # BaseRepository[Usuario]
uow.roles                 # BaseRepository[Rol]
uow.refresh_tokens        # BaseRepository[RefreshToken]
uow.direcciones_entrega   # BaseRepository[DireccionEntrega]
uow.categorias            # BaseRepository[Categoria]
uow.productos             # BaseRepository[Producto]
uow.ingredientes          # BaseRepository[Ingrediente]
uow.producto_categorias   # BaseRepository[ProductoCategoria]
uow.producto_ingredientes # BaseRepository[ProductoIngrediente]
uow.estados_pedido        # BaseRepository[EstadoPedido]
uow.formas_pago           # BaseRepository[FormaPago]
uow.pedidos               # BaseRepository[Pedido]
uow.detalles_pedido       # BaseRepository[DetallePedido]
uow.historial_estado_pedido # BaseRepository[HistorialEstadoPedido]
uow.pagos                 # BaseRepository[Pago]
```

### Atomicity Guarantee

```python
try:
    async with uow:
        user_1 = await uow.usuarios.create(usuario_1)
        # If this raises IntegrityError (duplicate email):
        user_2 = await uow.usuarios.create(usuario_2)
        # Both user_1 and user_2 are ROLLED BACK
except IntegrityError:
    # Neither user is in the database
    pass
```

### FastAPI Dependency

Use `Depends(get_uow)` to inject UnitOfWork into route handlers:

```python
from fastapi import Depends
from backend.infrastructure import get_uow, UnitOfWork

@app.post("/api/v1/usuarios")
async def create_user(
    user_data: UserCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    async with uow:
        new_user = Usuario(**user_data.dict())
        user = await uow.usuarios.create(new_user)
        return user
```

---

## Authentication Dependencies

### Overview

Provides FastAPI dependencies for JWT token extraction, validation, and current user resolution.

### Location

```
backend/infrastructure/dependencies.py
```

### Dependencies

#### `extract_token()`

Extracts JWT token from `Authorization: Bearer <token>` header.

```python
# Raises 401 if header missing or malformed
async def extract_token(auth_header: Optional[str] = Header(...)) -> str
```

#### `verify_token_dependency()`

Verifies JWT signature and expiration using `core.security.verify_token()`.

```python
async def verify_token_dependency(token: str = Depends(extract_token)) -> dict[str, Any]
```

#### `get_current_user()`

Resolves current authenticated user from JWT token.

```python
async def get_current_user(
    payload: dict = Depends(verify_token_dependency),
    uow: UnitOfWork = Depends(get_uow),
) -> Usuario
```

**Raises:**
- `401 Unauthorized`: If user not found or token invalid
- `403 Forbidden`: If user is soft-deleted (`eliminado_en IS NOT NULL`)

### Usage

```python
from backend.infrastructure import get_current_user

@app.get("/api/v1/profile")
async def get_profile(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "rol": current_user.rol.nombre if current_user.rol else None,
    }
```

---

## RBAC Factory - Role-Based Access Control

### Overview

`require_role()` is a factory function that creates role-based access control dependencies. It validates that the current user has at least one of the specified roles.

### Location

```
backend/infrastructure/dependencies.py
```

### API

```python
def require_role(allowed_roles: list[str]) -> Callable
```

### Usage

```python
from backend.infrastructure import require_role, get_current_user

@app.post("/api/v1/productos")
async def create_product(
    data: ProductCreate,
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(require_role(["ADMIN", "STOCK"]))
):
    # Only users with ADMIN or STOCK role reach here
    # Others get 403 Forbidden
    pass
```

### Multiple Roles (OR logic)

```python
# User needs at least ONE of these roles
_ = Depends(require_role(["ADMIN", "STOCK", "PEDIDOS"]))

# If user has ADMIN role → allowed ✓
# If user has STOCK role → allowed ✓
# If user has CLIENT role → 403 Forbidden ✗
```

### Error Response

```json
{
  "type": "https://foodstore.example.com/errors/authorization-error",
  "title": "Insufficient Permissions",
  "status": 403,
  "detail": "Insufficient permissions. Required roles: ADMIN, STOCK",
  "instance": "/api/v1/productos"
}
```

---

## RFC 7807 Error Middleware

### Overview

Global exception handler that formats all errors as RFC 7807 Problem+JSON responses. Provides standardized error structure across all endpoints.

### Location

```
backend/infrastructure/error_middleware.py
```

### Response Structure

All errors follow RFC 7807 format:

```json
{
  "type": "https://foodstore.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "instance": "/api/v1/usuarios",
  "errors": {
    "email": ["Invalid email format"],
    "password": ["Ensure this value has at least 8 characters"]
  }
}
```

### Standard Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | URI | Yes | Machine-readable error category |
| `title` | String | Yes | Short error description |
| `status` | Integer | Yes | HTTP status code |
| `detail` | String | Yes | Human-readable explanation |
| `instance` | URI | No | Request path |
| `errors` | Object | No | Field-level validation errors |

### Error Categories

| Status | Type | Category | Example |
|--------|------|----------|---------|
| 400 | `validation-error` | Bad request | Malformed JSON |
| 401 | `authentication-error` | Auth failed | Invalid token |
| 403 | `authorization-error` | Insufficient role | Forbidden role |
| 404 | `not-found` | Resource missing | Product not found |
| 409 | `conflict` | Constraint violation | Duplicate email |
| 500 | `internal-server-error` | Server error | Unhandled exception |

### Content-Type

All error responses set `Content-Type: application/problem+json`.

### Stack Traces

- **Non-500 errors:** Stack traces NOT included in response
- **500 errors:** Full stack trace logged server-side, but NOT returned to client

---

## Integration Patterns

### Pattern 1: Service Layer with UnitOfWork

```python
# backend/services/product_service.py

async def create_product_with_categories(
    product_data: CreateProductRequest,
    uow: UnitOfWork,
) -> Producto:
    """Create product and assign to categories (atomic operation)."""
    async with uow:
        # Check product doesn't already exist
        existing = await uow.productos.execute_query(
            select(Producto).where(Producto.nombre == product_data.nombre)
        )
        if existing:
            raise ProductAlreadyExistsError()
        
        # Create product
        product = Producto(**product_data.dict())
        await uow.productos.create(product)
        
        # Add to categories
        for categoria_id in product_data.categoria_ids:
            categoria = await uow.categorias.get_by_id(categoria_id)
            if not categoria:
                raise CategoriaNotFoundError()
            
            pc = ProductoCategoria(
                producto_id=product.id,
                categoria_id=categoria_id,
            )
            await uow.producto_categorias.create(pc)
        
        # Both product creation and category assignments commit together
        return product
```

### Pattern 2: Protected Routes with RBAC

```python
# backend/routes/products.py

from fastapi import APIRouter, Depends
from backend.infrastructure import get_current_user, require_role, get_uow
from backend.core.models import Usuario

router = APIRouter(prefix="/api/v1/productos", tags=["Productos"])

@router.post("")
async def create_product(
    data: ProductCreate,
    current_user: Usuario = Depends(get_current_user),
    _ = Depends(require_role(["ADMIN", "STOCK"])),
    uow: UnitOfWork = Depends(get_uow),
):
    """Create a new product (ADMIN or STOCK only)."""
    # current_user available for logging/audit
    # uow available for database operations
    pass

@router.get("/{product_id}")
async def get_product(product_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get product (public)."""
    async with uow:
        product = await uow.productos.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
```

### Pattern 3: Error Handling

All exceptions automatically converted to RFC 7807:

```python
# HTTPException
raise HTTPException(
    status_code=409,
    detail="Email already registered"
)
# → 409 Conflict response

# Pydantic ValidationError
# → 400 Bad Request with field errors

# Database IntegrityError
# → 409 Conflict response

# Unhandled Exception
# → 500 Internal Server Error (stack trace logged, not sent to client)
```

---

## Directory Structure

```
backend/
├── infrastructure/
│   ├── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── base_repository.py        # Generic[T] repository
│   ├── dependencies.py                # Auth + RBAC dependencies
│   ├── uow.py                         # UnitOfWork pattern
│   └── error_middleware.py            # RFC 7807 handler
├── core/
│   ├── models.py                      # SQLModel entities
│   ├── security.py                    # JWT + password hashing
│   └── database.py                    # AsyncSession + engine
├── tests/
│   ├── test_base_repository.py
│   ├── test_uow.py
│   ├── test_dependencies.py
│   └── test_error_middleware.py
└── main.py                            # FastAPI app + error handler registration
```

---

## Testing

All infrastructure components have comprehensive unit and integration tests:

```bash
# Unit tests (mocked AsyncSession)
pytest tests/test_base_repository.py -v

# Unit tests (async context manager)
pytest tests/test_uow.py -v

# Auth dependencies
pytest tests/test_dependencies.py -v

# Error middleware
pytest tests/test_error_middleware.py -v

# All tests with coverage
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## Best Practices

1. **Always use UnitOfWork for multi-step operations** to ensure atomicity
2. **Protect admin routes with `require_role()`** for access control
3. **Let the error middleware handle exceptions** - don't catch and re-raise unless needed
4. **Use soft-delete, not hard-delete** for business entities (compliance/audit)
5. **Type hint everything** - `BaseRepository[T]` provides compile-time safety
6. **Cache repositories in UnitOfWork** to avoid redundant instantiation
7. **Log errors server-side** - stack traces are never sent to clients

