## Why

The food store backend has authentication, RBAC, categories, and ingredients implemented, but the core `Producto` entity has no REST API yet. The frontend catalog UI exists but calls endpoints that don't exist, causing INC-01 (deuda técnica). This change implements the full CRUD API for products so the catalog can display real data.

## What Changes

- `GET /api/v1/productos` — paginated list, public, excludes soft-deleted by default; `?incluir_eliminados=true` requires STOCK or ADMIN (RN-CA10)
- `GET /api/v1/productos/{id}` — single product, public
- `POST /api/v1/productos` — create product, requires STOCK or ADMIN
- `PUT /api/v1/productos/{id}` — full update, requires STOCK or ADMIN
- `DELETE /api/v1/productos/{id}` — soft delete (`eliminado_en`), requires STOCK or ADMIN
- `PATCH /api/v1/productos/{id}/stock` — update stock only, requires STOCK or ADMIN
- New `ProductoRepository` class registered in `UnitOfWork` (replaces the current raw `BaseRepository[Producto]`)
- New Alembic migration adding a partial index on `productos.nombre WHERE eliminado_en IS NULL`
- Full unit + integration tests in `backend/tests/test_productos.py`

## Capabilities

### New Capabilities

- `products-crud`: Full CRUD REST API for the Producto entity — create, read, update, soft-delete, stock patch — with role-based access control and soft-delete filtering.

### Modified Capabilities

- (none — Producto model already exists in `core/models.py`; no schema-level requirement changes)

## Impact

- **Files created**: `backend/productos/repository.py`, `backend/productos/service.py`, `backend/productos/router.py`, `backend/alembic/versions/008_add_productos_index.py`, `backend/tests/test_productos.py`
- **Files modified**: `backend/infrastructure/uow.py` (replace `BaseRepository[Producto]` with `ProductoRepository`), `backend/main.py` (register `productos_router`)
- **Files already exist**: `backend/productos/schemas.py` (complete, no changes needed), `backend/productos/__init__.py`
- **API surface**: 6 new endpoints under `/api/v1/productos`
- **Dependencies**: `route-protection-rbac` (provides `require_role`), `ingredients-crud-allergens` (last archived change)
