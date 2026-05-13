## Context

The `ProductoCategoria` N:M pivot table already exists in `backend/core/models.py` and is created by the initial Alembic migration. However, the `productos` module (`backend/productos/`) has no endpoints, service functions, or repository methods to manage these associations. The `categories-crud-hierarchical` change introduced `GET/POST/PUT/DELETE /api/v1/categorias` but did not add the product-side endpoints for linking. This change fills that gap by adding sub-resource endpoints under `/api/v1/productos/{id}/categorias`.

The existing architecture is:
- `Router → Service → UoW → Repository → Model` (unidireccional, no invertir)
- `ProductoCategoria(producto_id PK, categoria_id PK)` — composite PK, no extra columns
- `UnitOfWork` in `infrastructure/uow.py` exposes named repository attributes
- `BaseRepository[T]` in `core/` provides `create`, `hard_delete`, `list_all`

## Goals / Non-Goals

**Goals:**
- Add `GET /api/v1/productos/{id}/categorias` — public, lists assigned categories
- Add `PUT /api/v1/productos/{id}/categorias` — atomic full-replacement of category set (ADMIN or STOCK)
- Add `DELETE /api/v1/productos/{id}/categorias/{categoria_id}` — remove one association (ADMIN or STOCK)
- Enrich `ProductoResponse` with a `categorias: list[CategoriaCompacta]` field (additive, non-breaking)
- Extend `ProductoRepository` (or add a `ProductoCategoriaRepository`) with pivot-table query methods
- Register new repository in `UnitOfWork`

**Non-Goals:**
- Bulk-create individual associations one by one (PUT replaces the full set atomically)
- Exposing category soft-delete guard (RN-CA03) — belongs to the categories module; not implemented here
- Frontend changes — this change is backend-only
- Pagination of the category list for a product (a product is expected to have few categories)

## Decisions

### D-01: PUT replaces the full set (not PATCH append)

**Decision**: `PUT /api/v1/productos/{id}/categorias` with body `{ "categoria_ids": [1, 2, 3] }` deletes all existing rows in `producto_categoria` for the product and inserts the new set atomically via UoW.

**Rationale**: The Integrador spec (US-016) and CHANGES.md describe this as a full-replacement PUT, matching the idempotent semantics of HTTP PUT on a collection sub-resource. An empty array `[]` means "remove all". This avoids complex diff logic and is consistent with how similar pivots are handled in the project (e.g., UsuarioRol).

**Alternatives considered**: PATCH append/remove — more granular but adds complexity; a separate DELETE endpoint already handles single removals.

### D-02: Repository methods added directly to `ProductoRepository`

**Decision**: Add pivot-table methods (`set_categorias`, `get_categorias`, `remove_categoria`) as methods on a `ProductoCategoriaRepository` class, and register it as `uow.producto_categorias` in the UoW.

**Rationale**: Keeps the `ProductoRepository` focused on the `Producto` entity. The pivot table `ProductoCategoria` is its own model; a dedicated repository is consistent with `IngredienteRepository` / `ProductoIngredienteRepository` patterns already present in the codebase.

**Alternatives considered**: Adding methods directly to `ProductoRepository` — simpler, but mixes concerns when querying the pivot vs. the product entity.

### D-03: Validate categoria_ids existence in Service

**Decision**: Before inserting pivot rows, `ProductosService` calls `uow.categorias.get_by_id(cat_id)` for each ID in the request. Any non-existent or soft-deleted category raises `HTTP 404`.

**Rationale**: Keeps business-rule validation in the Service layer (not Repository), consistent with existing patterns. The Repository only performs the INSERT; the Service owns the "does this category exist?" check.

### D-04: ProductoResponse enriched with categorias field, default empty list

**Decision**: `ProductoResponse` gains `categorias: list[CategoriaCompacta] = []`. `CategoriaCompacta` contains `id`, `nombre`, and `padre_id` only.

**Rationale**: Existing callers of `GET /api/v1/productos/{id}` receive a new field with a safe default. No breaking change. The detail endpoint already joins to related data (this change simply adds the category join). The list endpoint (`GET /api/v1/productos`) does NOT eagerly load categories to avoid N+1 on bulk listings.

### D-05: No Alembic migration needed

**Decision**: The `producto_categoria` table already exists from the initial migration. No schema changes are required.

**Rationale**: The `ProductoCategoria` SQLModel is already in `core/models.py` and included in the initial `alembic upgrade head`. This change is purely application-layer.

## Risks / Trade-offs

- **N+1 on product detail enrichment** → Mitigation: Use `selectinload` or a single `SELECT … JOIN` when loading categories for a single product; only for `GET /api/v1/productos/{id}`, not the list endpoint.
- **Race conditions on PUT full-replacement** → Mitigation: The UoW wraps DELETE + INSERT in a single transaction; concurrent requests may see the window between delete and insert as "empty", but atomicity is guaranteed at commit time.
- **Empty categoria_ids accepted** → Intentional: `PUT` with `[]` removes all associations, which is valid business behavior.

## Migration Plan

1. No database migration required.
2. Deploy backend with new endpoints.
3. Existing `GET /api/v1/productos/{id}` responses will include `categorias: []` for products with no associations — safe additive field.
4. Rollback: remove the 3 new router endpoints and revert `ProductoResponse` schema; no data is deleted.

## Open Questions

- None. The pivot table, models, and UoW pattern are established. Implementation is straightforward.
