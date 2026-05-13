## Why

Products are stored in `productos` but have no way to be classified into categories at the API level. The `ProductoCategoria` pivot table exists in the database model but there are no endpoints to manage these associations. Without this change, the product catalog cannot be filtered by category, the product detail does not expose which categories a product belongs to, and the category deletion guard (RN-CA03: cannot delete a category with active associated products) cannot function correctly.

## What Changes

- New sub-resource endpoints under `/api/v1/productos/{id}/categorias` to manage N:M associations
- `PUT /api/v1/productos/{id}/categorias` — full replacement of all categories for a product (idempotent, body: `{ "categoria_ids": [int, ...] }`)
- `DELETE /api/v1/productos/{id}/categorias/{categoria_id}` — remove a single category from a product
- `GET /api/v1/productos/{id}/categorias` — list categories currently assigned to a product (public)
- The `ProductoResponse` schema already returned by `GET /api/v1/productos/{id}` will be enriched to include the list of assigned categories
- A new `ProductoCategoriaRepository` will handle all pivot-table queries in the `productos` module
- The UoW will expose the new repository for use by the `ProductosService`

## Capabilities

### New Capabilities

- `products-categories-association`: CRUD-style management of the N:M relationship between products and categories via the `producto_categoria` pivot table. Includes listing assigned categories, replacing the full set of associations atomically, and removing a single association.

### Modified Capabilities

- `products-crud`: The `ProductoResponse` (GET /api/v1/productos/{id}) gains a `categorias` field with the list of categories assigned to the product. This is a non-breaking additive change to the response schema.

## Impact

- **Backend — new files**: `backend/productos/repository.py` gains `ProductoCategoriaRepository` methods (or a dedicated mixin); `backend/productos/service.py` gains new service functions; `backend/productos/router.py` gains 3 new endpoints; `backend/productos/schemas.py` gains `CategoriaCompacta` and `ProductoCategoriaSetRequest` schemas.
- **Backend — models**: No model changes needed — `ProductoCategoria` already exists in `backend/core/models.py`.
- **Backend — UoW**: `ProductoCategoriaRepository` registered in `infrastructure/uow.py`.
- **Alembic migration**: Not required — `producto_categoria` table is already created by the existing migration.
- **Tests**: New test file `backend/tests/test_productos_categorias.py` covering the 3 endpoints.
- **Downstream**: `DELETE /api/v1/categorias/{id}` soft-delete guard (RN-CA03) now can check `producto_categoria` rows before allowing deletion.
