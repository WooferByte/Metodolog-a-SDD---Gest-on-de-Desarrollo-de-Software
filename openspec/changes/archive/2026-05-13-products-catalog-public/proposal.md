## Why

The public product catalog endpoint (`GET /api/v1/productos`) already exists but only supports pagination and allergen exclusion. Clients need to discover products by text search and category, which are core catalog navigation flows defined in HU-018 (US-018) and required for the frontend catalog grid with debounce/filters (rúbrica: 15 pts).

## What Changes

- `GET /api/v1/productos`: add `?q=` (ILIKE search on nombre and descripcion) and `?categoria_id=` (filter by category) query parameters. Pagination via `?page=` / `?size=` added alongside existing `skip`/`limit` (spec convention: `page=1&size=20`).
- `ProductoRepository.list_active`: extend to accept `q` (text search) and `categoria_id` (join filter) parameters. Existing `incluir_eliminados` and `excluirAlergenos` filters remain unchanged.
- `service.list_productos`: forward new parameters to the repository method.
- Response format for the list endpoint changes to paginated envelope: `{ "items": [...], "total": N, "page": 1, "size": 20, "pages": P }` as specified in Integrador.txt §5 convention. This is a **BREAKING** change for existing consumers of the list endpoint (currently returns a flat list).
- New `PaginatedProductosResponse` schema added to `productos/schemas.py`.
- `GET /api/v1/productos/{id}`: already returns `categorias` and `ingredientes` — no structural changes needed. Verify `disponible=true` filter on public access (RN-CA08).
- Tests added for: `?q=` search (match, no-match), `?categoria_id=` filter (match, no-match, invalid), combined filters, and paginated response shape.

## Capabilities

### New Capabilities

- `products-catalog-public`: Public catalog search and filtering — ILIKE text search on `nombre`/`descripcion`, filter by `categoria_id`, paginated response envelope (`items`, `total`, `page`, `size`, `pages`).

### Modified Capabilities

- `products-crud`: The list endpoint (`GET /api/v1/productos`) changes its response from `list[ProductoResponse]` to a paginated envelope, and adds two new optional query params (`q`, `categoria_id`). Existing `skip`, `limit`, `incluir_eliminados`, and `excluirAlergenos` params remain supported.

## Impact

- **Backend files modified**: `backend/productos/router.py`, `backend/productos/service.py`, `backend/productos/repository.py`, `backend/productos/schemas.py`
- **No new DB tables or Alembic migration** (filters operate on existing tables `producto`, `producto_categoria`)
- **No frontend changes** in this change (frontend catalog UI is a separate change)
- **Breaking change**: list response envelope changes from flat `list` to paginated `{ items, total, page, size, pages }`. Admin dashboard and any existing tests that consume the flat list must be updated.
- **Existing tests affected**: `backend/tests/test_productos.py` assertions on list response shape must be updated to expect the paginated envelope.
