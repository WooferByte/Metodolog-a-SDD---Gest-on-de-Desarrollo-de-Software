## Why

The product catalog requires a hierarchical category system so that items can be organized under parent categories (e.g., "Bebidas" > "Bebidas Calientes"). Without it, the products CRUD and the frontend catalog have no taxonomy backbone — they depend on `categorias` as a prerequisite. This change also closes INC-01 partially by providing the backend CRUD that the catalog UI was archived without.

## What Changes

- New module `backend/categorias/` — `model.py` already exists in `core/models.py`; this change adds `repository.py`, `service.py`, and `router.py`
- New `CategoriaRepository` extending `BaseRepository[Categoria]` with a raw CTE method `get_tree()` for recursive subtree queries
- New `CategoriaService` implementing CRUD + anti-cycle + active-products guard (soft delete)
- New `APIRouter` mounted at `/api/v1/categorias` with 5 endpoints: list, create, get, update, delete
- New Alembic migration `006_add_categoria_indexes.py` — index on `padre_id` for CTE join performance
- New `backend/tests/test_categorias.py` — unit tests for service layer (mock UoW) and router integration tests
- `backend/main.py` — include the new router

## Capabilities

### New Capabilities

- `categories-crud`: CRUD REST endpoints for `Categoria` with hierarchical tree support (POST, GET list, GET by id, GET tree, PUT, DELETE/soft). Includes anti-cycle validation and guard against deleting categories with active products.

### Modified Capabilities

<!-- No existing capabilities have requirement-level changes in this change -->

## Impact

- **Backend**: New files in `backend/categorias/` (repository, service, router), one new migration, one new test file, one change to `main.py`
- **API**: New routes at `/api/v1/categorias` — GET endpoints are public; POST/PUT/DELETE require role `STOCK` or `ADMIN`
- **Database**: No new columns/tables — `categorias` table already exists from migration 001. New index on `padre_id`
- **Frontend**: Unblocks product assignment to categories (future change `products-crud-core`)
- **Dependencies upstream**: Requires `route-protection-rbac` to be complete (RBAC guards already deployed)
