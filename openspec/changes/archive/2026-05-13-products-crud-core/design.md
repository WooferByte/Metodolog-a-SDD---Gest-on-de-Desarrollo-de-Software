## Context

The `Producto` SQLModel is defined in `backend/core/models.py` with fields: `id`, `nombre`, `descripcion`, `precio_base` (NUMERIC 10,2), `stock_cantidad` (INTEGER ≥ 0), `disponible` (bool), `imagen_url`, `creado_en`, `actualizado_en`, `eliminado_en`.

`backend/productos/schemas.py` already exists with `ProductoCreate`, `ProductoUpdate`, and `ProductoResponse` — no changes needed.

The UoW currently exposes `uow.productos` as a plain `BaseRepository[Producto]`. The pattern established by `CategoriaRepository` and `IngredienteRepository` requires a dedicated repository class for each entity that needs custom query methods. `Producto` needs a `list_active` with optional `incluir_eliminados` filter.

The architecture contract (Router → Service → UoW → Repository → Model) is non-negotiable and must be respected exactly.

## Goals / Non-Goals

**Goals:**
- Implement 6 REST endpoints for Producto CRUD
- Create `ProductoRepository` extending `BaseRepository[Producto]` with a `list_active` method
- Register `ProductoRepository` in `UnitOfWork.productos` (replacing the current `BaseRepository[Producto]`)
- Soft delete via `eliminado_en` — never hard delete
- `?incluir_eliminados=true` query param on GET list — accessible only with STOCK or ADMIN (RN-CA10)
- Separate `PATCH /productos/{id}/stock` endpoint for stock-only updates
- Alembic migration for partial index on `productos.nombre WHERE eliminado_en IS NULL`
- Unit and integration tests following the `test_categorias.py` pattern

**Non-Goals:**
- Category/ingredient associations (handled in `products-categories-association` and `products-ingredients-association`)
- Frontend changes
- Full-text search on nombre
- Pagination metadata in response body (only `skip`/`limit` query params)

## Decisions

### D1: ProductoRepository vs. BaseRepository inline

**Decision**: Create `backend/productos/repository.py` with `ProductoRepository(BaseRepository[Producto])`.

**Rationale**: Every module that needs custom queries has its own repository class (see `CategoriaRepository`, `IngredienteRepository`). Using `BaseRepository[Producto]` directly in UoW breaks the convention and prevents adding the `list_active` method with `incluir_eliminados` support. `BaseRepository.list_all()` always excludes soft-deleted — it cannot support RN-CA10.

**Alternative considered**: Add `incluir_eliminados` param to `BaseRepository.list_all()` — rejected because it would pollute the generic class with domain-specific behavior.

### D2: ORM queries (not raw SQL) for list_active

**Decision**: Use SQLAlchemy ORM `select(Producto).where(...).offset(...).limit(...)` for `list_active`.

**Rationale**: Raw SQL with `.mappings()` fails to reconstruct SQLModel objects correctly (known bug from prior changes). The ORM approach is type-safe and consistent with `IngredienteRepository.list_by_alergeno`.

**Alternative considered**: Raw SQL with `text()` — rejected because it bypasses SQLModel ORM mapping and causes runtime errors when constructing response objects.

### D3: include_deleted permission enforcement in Service (not Router)

**Decision**: The `incluir_eliminados` flag is passed from router to service; service checks the user's roles to validate permission.

**Rationale**: Business rules live in the service layer. The router passes `current_user` (optional, resolved by FastAPI DI) alongside the flag. If `incluir_eliminados=True` and the user is not STOCK/ADMIN, the service raises HTTP 403.

**Alternative considered**: Enforce in the router via a separate `Depends(require_role(...))` — this works but creates two different auth paths for the same endpoint. Handling in service is cleaner and testable without HTTP.

### D4: PATCH /productos/{id}/stock as a distinct endpoint

**Decision**: Separate `PATCH` endpoint at `/api/v1/productos/{id}/stock` with a minimal `ProductoStockUpdate` schema (`stock_cantidad: int ≥ 0`).

**Rationale**: Spec requires a dedicated stock endpoint (STOCK or ADMIN only). Separating it from the general `PUT` makes intent explicit and allows different permission semantics in future.

### D5: Alembic migration — partial index on nombre

**Decision**: Migration `008_add_productos_index.py` adds `CREATE INDEX IF NOT EXISTS idx_productos_nombre_active ON productos (nombre) WHERE eliminado_en IS NULL`.

**Rationale**: Consistent with migration 006 (categorias) and 007 (ingredientes). Accelerates lookup by nombre for active products.

## Risks / Trade-offs

- **Risk**: `list_active` with `incluir_eliminados=True` returns all products including deleted; service must enforce role check or deleted products are leaked to public.
  → **Mitigation**: Service raises HTTP 403 if `incluir_eliminados=True` and user is None or lacks STOCK/ADMIN role.

- **Risk**: `actualizado_en` not updated on PATCH stock.
  → **Mitigation**: `BaseRepository.update()` automatically sets `actualizado_en` via `hasattr(entity, "actualizado_en")` check.

- **Risk**: UoW `productos` property currently returns `BaseRepository[Producto]`. Changing to `ProductoRepository` could silently break callers that expected the base type.
  → **Mitigation**: `ProductoRepository` extends `BaseRepository[Producto]`, so all existing callers get a superset. No breaking change.

## Migration Plan

1. Create `backend/productos/repository.py`
2. Create `backend/productos/service.py`
3. Create `backend/productos/router.py`
4. Update `backend/infrastructure/uow.py` — replace `BaseRepository(self.session, Producto)` with `ProductoRepository(self.session)`
5. Update `backend/main.py` — add `from productos.router import router as productos_router` and `app.include_router(productos_router, prefix="/api/v1")`
6. Create `backend/alembic/versions/008_add_productos_index.py`
7. Create `backend/tests/test_productos.py`
8. Verify: `python -c "from main import app; print('OK')"` + `pytest tests/ -x -q`

**Rollback**: Remove router import from `main.py`; revert `uow.py` to `BaseRepository(self.session, Producto)`.

## Open Questions

- (none — all business rules from RN-CA10 and the spec are clear)
