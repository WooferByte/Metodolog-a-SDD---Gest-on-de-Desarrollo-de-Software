# Unit of Work Pattern Capability

## Overview

Async context manager that coordinates multiple repositories in a single database transaction. Ensures atomicity: either all changes commit together, or all rollback.

## ADDED Requirements

#### Scenario: Create product with categories in atomic transaction
```python
async with UnitOfWork(session) as uow:
    # Both operations succeed or both fail together
    new_product = Producto(nombre="Pizza", precio_base=Decimal("25.00"))
    await uow.productos.create(new_product)
    
    category = await uow.categorias.get_by_id(1)
    await uow.producto_categoria.create(
        ProductoCategoria(producto_id=new_product.id, categoria_id=category.id)
    )
    # Auto-commits on successful exit
```

#### Scenario: Rollback on error
```python
try:
    async with UnitOfWork(session) as uow:
        await uow.usuarios.create(usuario_1)
        # If this raises an exception:
        await uow.usuarios.create(usuario_2)  # raises due to duplicate email
        # Both creates are rolled back
except IntegrityError:
    # usuarios_1 and usuarios_2 NOT in database
    pass
```

#### Scenario: Multiple independent transactions
```python
# Transaction 1
async with UnitOfWork(session1) as uow1:
    await uow1.productos.create(product1)

# Transaction 2 (separate session)
async with UnitOfWork(session2) as uow2:
    await uow2.pedidos.create(order1)
```

## Requirements

### R1: Context Manager Protocol
- `async def __aenter__(self) -> UnitOfWork`
  - Initializes all repository attributes (lazy or eager)
  - Starts transaction
  - Returns self for `as uow:` binding
- `async def __aexit__(self, exc_type, exc_val, exc_tb) -> None`
  - If no exception: `await session.commit()`
  - If exception: `await session.rollback()`
  - Always closes session

### R2: Repository Attributes
- `self.usuarios: BaseRepository[Usuario]`
- `self.refresh_tokens: BaseRepository[RefreshToken]`
- `self.direcciones: BaseRepository[DireccionEntrega]`
- `self.categorias: BaseRepository[Categoria]`
- `self.productos: BaseRepository[Producto]`
- `self.ingredientes: BaseRepository[Ingrediente]`
- `self.producto_categoria: BaseRepository[ProductoCategoria]`
- `self.producto_ingrediente: BaseRepository[ProductoIngrediente]`
- `self.estados_pedido: BaseRepository[EstadoPedido]`
- `self.pedidos: BaseRepository[Pedido]`
- `self.detalle_pedido: BaseRepository[DetallePedido]`
- `self.historial_estado_pedido: BaseRepository[HistorialEstadoPedido]`
- `self.formas_pago: BaseRepository[FormaPago]`
- `self.pagos: BaseRepository[Pago]`

### R3: Transaction Boundaries
- Single `AsyncSession` shared by all repositories
- All repositories operate on same transaction
- Atomicity guaranteed: all-or-nothing
- Rollback automatic on any exception in `async with` block

### R4: Dependency Injection Support
- `async def get_uow(session: AsyncSession = Depends(get_db)) -> UnitOfWork`
- FastAPI dependency that injects UoW into route handlers
- Usage: `@app.post("/api/v1/pedidos") async def create_order(uow: UnitOfWork = Depends(get_uow))`

### R5: Error Propagation
- Exceptions raised inside `async with` block propagate normally
- Caller catches exceptions, not UoW itself
- UoW's job is transactional cleanup, not error handling

### R6: No Nested Transactions
- Creating UoW inside existing transaction should reuse parent session (optional)
- Or raise error if nesting detected (simpler implementation)

## Acceptance Criteria

- [ ] UnitOfWork class created with async context manager protocol
- [ ] All 14 repository attributes present and typed
- [ ] Auto-commit on successful exit
- [ ] Auto-rollback on exception
- [ ] Dependency injection works with FastAPI
- [ ] Atomicity verified with integration tests
- [ ] Thread/task-safe (each request gets own session)
