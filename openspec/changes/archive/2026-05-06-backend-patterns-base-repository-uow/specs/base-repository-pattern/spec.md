# Base Repository Pattern Capability

## Overview

Generic repository implementation for all SQLModel entities using DDD principles. Provides CRUD operations with automatic soft-delete filtering.

## ADDED Requirements

#### Scenario: Create and retrieve product
```python
# Create
produto_repo = BaseRepository[Produto](session, Produto)
new_product = Produto(nome="Pizza", preco_base=Decimal("25.00"), stock_cantidad=10)
await product_repo.create(new_product)

# Retrieve
retrieved = await product_repo.get_by_id(new_product.id)
assert retrieved.id == new_product.id
```

#### Scenario: List all active products (soft-delete excluded)
```python
products = await product_repo.list_all()
# Returns only products where eliminado_en IS NULL
```

#### Scenario: Soft-delete a product
```python
await product_repo.soft_delete(product_id=1)
# Sets eliminado_en = NOW() instead of DELETE
```

#### Scenario: Update product stock
```python
product = await product_repo.get_by_id(1)
product.stock_cantidad = 5
await product_repo.update(product)
```

## Requirements

### R1: Generic Type Safety
- `BaseRepository[T]` where `T` is SQLModel entity
- Constructor: `__init__(session: AsyncSession, model_class: type[T])`
- Type hints ensure compile-time safety

### R2: Create Operation
- `async def create(entity: T) -> T`
- Adds entity to session, flushes, returns entity with ID populated
- Idempotent: safe to call multiple times with same entity

### R3: Read Operations
- `async def get_by_id(entity_id: int) -> Optional[T]`
  - Excludes soft-deleted records (`eliminado_en IS NULL`)
- `async def list_all(skip: int = 0, limit: int = 100) -> list[T]`
  - Excludes soft-deleted records
  - Supports pagination
- `async def count() -> int`
  - Returns total count of active (non-deleted) records

### R4: Update Operation
- `async def update(entity: T) -> T`
- Merges entity into session, flushes, returns updated entity
- Updates `actualizado_en` timestamp (if entity has it)

### R5: Soft-Delete Operation
- `async def soft_delete(entity_id: int) -> None`
- Sets `eliminado_en = NOW()` instead of hard delete
- Soft-deleted records excluded from all queries by default

### R6: Hard-Delete Operation
- `async def hard_delete(entity_id: int) -> None`
- Actual DELETE from database (use sparingly, compliance only)
- Not exposed to normal repository queries

### R7: Query Builder Support
- `async def execute_query(query: Select) -> list[T]`
  - Raw SQLAlchemy Select query execution
  - Allows complex WHERE/JOIN/GROUP BY operations
- `async def execute_scalar(query: Select) -> Any`
  - Execute scalar query (COUNT, aggregate functions, etc.)

### R8: Soft-Delete Automatic Filtering
- All list/count queries automatically append `WHERE eliminado_en IS NULL`
- No exceptions: even if querying soft-deleted records is needed, use raw `execute_query()`

## Acceptance Criteria

- [ ] BaseRepository[T] generic class created
- [ ] All 8 methods implemented and typed
- [ ] Soft-delete filtering works for all queries
- [ ] Timestamps (creado_en, actualizado_en) updated automatically
- [ ] Type hints prevent runtime errors
- [ ] Works with all 15 SQLModel entities
- [ ] No hard-coded model assumptions (truly generic)
