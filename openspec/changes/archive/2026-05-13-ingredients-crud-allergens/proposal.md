## Why

The Food Store backend needs an ingredient management system so that product composition can be tracked and allergen information can be exposed to customers. This change implements the full CRUD API for ingredients, satisfying Epic 02 (Catálogo) requirements defined in `docs/Integrador.txt`.

## What Changes

- Add `IngredienteRepository` with `has_active_products()` guard check
- Add `IngredienteService` with list/get/create/update/soft-delete business logic
- Add `IngredienteRouter` exposing `GET/POST/PUT/DELETE /api/v1/ingredientes`
- Register router in `backend/main.py`
- Create Alembic migration `007_add_ingredientes_index.py` to add partial index on `ingredientes.nombre` for allergen filter queries
- Write unit tests in `backend/tests/test_ingredientes.py`

## Capabilities

### New Capabilities

- `ingredientes-crud`: Full CRUD for `Ingrediente` model — create, list (with `?es_alergeno` filter), get by ID, partial update, soft-delete with active-products guard. Includes allergen flag (`es_alergeno: bool`), `UNIQUE` constraint on `nombre`, and `eliminado_en` soft-delete.

### Modified Capabilities

<!-- None — no existing spec-level requirements change -->

## Impact

- **API**: New endpoints at `POST/GET /api/v1/ingredientes` and `GET/PUT/DELETE /api/v1/ingredientes/{id}`
- **Auth**: GET endpoints are public; POST/PUT/DELETE require `STOCK` or `ADMIN` role
- **Model**: `Ingrediente` model already exists in `core/models.py` — no schema change needed
- **DB**: Partial index migration needed for allergen filter performance
- **UoW**: `uow.ingredientes` already wired to `BaseRepository[Ingrediente]` — needs upgrade to `IngredienteRepository`
- **Tests**: New test file `backend/tests/test_ingredientes.py`
- **Downstream**: `products-crud-core` change depends on `ingredientes` being available
