## Context

The `GET /api/v1/productos` endpoint is live with: offset-based pagination (`skip`/`limit`), soft-delete guard (`incluir_eliminados`), and allergen exclusion (`excluirAlergenos`). The `ProductoRepository` has two query methods: `list_active` and `list_active_excluding_alergenos`. The service layer cleanly separates role guards from data retrieval.

What's missing: text search (`?q=` ILIKE on nombre/descripción) and category filter (`?categoria_id=`), required by US-018 and the frontend catalog grid. Additionally, the spec convention in Integrador.txt §5 mandates a paginated envelope `{ items, total, page, size, pages }` rather than a raw list — the current response is a flat list.

**Current tech stack**: FastAPI 0.109, SQLModel 0.0.14, asyncpg, Pydantic v2, PostgreSQL. Repository layer uses `select()` SQLAlchemy core expressions (not raw SQL).

## Goals / Non-Goals

**Goals:**
- Add `?q=` (ILIKE text search on `nombre` and `descripcion`) to `GET /api/v1/productos`
- Add `?categoria_id=` (join filter via `producto_categoria` pivot) to `GET /api/v1/productos`
- Migrate the list response to paginated envelope `{ items, total, page, size, pages }`
- Add `?page=` / `?size=` as canonical pagination params (alias for `skip`/`limit` with `size` default=20, max=100)
- Add `PaginatedProductosResponse` schema to `productos/schemas.py`
- Update `ProductoRepository.list_active` and `list_active_excluding_alergenos` to accept search/filter params
- Update existing tests to expect the new envelope shape
- Add new test coverage for search and category filter scenarios

**Non-Goals:**
- Full-text search (PostgreSQL `tsvector`) — ILIKE is sufficient for the rúbrica
- `?sort=` ordering beyond the existing `ORDER BY nombre` default
- Frontend catalog UI implementation (separate change)
- `?disponible=` filter (productos list already excludes `eliminado_en IS NOT NULL`; `disponible` filtering is a future concern)
- No Alembic migration needed (no schema changes)

## Decisions

### D-01: ILIKE search approach — ILIKE over `tsvector`

**Decision**: Use `ILIKE '%q%'` on `nombre` and `descripcion` columns, not PostgreSQL full-text search.

**Rationale**: ILIKE is deterministic, trivially testable in unit tests with mocks, and sufficient for the grading rubric. Full-text search would require a `tsvector` column, a migration, and `to_tsquery` query building — disproportionate complexity for the dataset size.

**Alternative considered**: `pg_trgm` trigram index with `%` ILIKE for better index use. Not needed at this dataset size; can be added via index-only migration later without API contract change.

**Implementation**:
```python
if q:
    pattern = f"%{q.strip()}%"
    stmt = stmt.where(
        or_(Producto.nombre.ilike(pattern), Producto.descripcion.ilike(pattern))
    )
```

### D-02: Category filter via JOIN vs subquery

**Decision**: Use a JOIN on `producto_categoria` pivot table to filter by `categoria_id`.

**Rationale**: A JOIN is more natural with the ORM query builder and avoids a subquery with `.in_()`. Since this is a filter (not an exclusion), JOIN + `DISTINCT` on the outer query is clean and readable.

**Alternative considered**: Subquery `WHERE producto.id IN (SELECT producto_id FROM producto_categoria WHERE categoria_id = X)`. Functionally equivalent but more verbose.

**Implementation**:
```python
if categoria_id is not None:
    stmt = (
        stmt
        .join(ProductoCategoria, ProductoCategoria.producto_id == Producto.id)
        .where(ProductoCategoria.categoria_id == categoria_id)
        .distinct()
    )
```

### D-03: Paginated envelope — new schema, keep backward compat on skip/limit

**Decision**: Add `PaginatedProductosResponse` schema. Change router return type from `list[ProductoResponse]` to `PaginatedProductosResponse`. Keep `skip`/`limit` params alongside new `page`/`size` params for backward compat with existing test setup.

**Rationale**: The spec mandates `{ items, total, page, size, pages }`. Breaking the flat list is unavoidable; it's listed as a breaking change in the proposal. The repository needs a `count` companion query to populate `total`.

**count query**: Use `SELECT COUNT(*) FROM ...` with the same WHERE clause (sans OFFSET/LIMIT) via `func.count()`.

### D-04: Unify list methods — single `list_active` vs separate methods

**Decision**: Merge `list_active` and `list_active_excluding_alergenos` into a single `list_active` that accepts all filter params (`q`, `categoria_id`, `alergeno_ids`, `incluir_eliminados`). Add a companion `count_active` method with the same filters.

**Rationale**: Having two separate methods was forced by the allergen filter complexity; with all params unified, one method is simpler to maintain and avoids duplicating the WHERE clause for the count query.

**Migration of existing call sites**: `service.list_productos` currently branches between the two methods; the branch is removed and both params are passed to the unified method.

### D-05: `disponible` filter on public list

**Decision**: The public list endpoint (`GET /api/v1/productos` without `incluir_eliminados`) SHALL filter `WHERE disponible = true` per RN-CA08. The current `list_active` only filters `eliminado_en IS NULL`. This is a correctness fix bundled in this change.

**Rationale**: RN-CA08 from Historias_de_usuario.txt states "El catálogo público solo muestra productos con disponible=true y eliminado_en IS NULL". The current implementation is incomplete.

## Risks / Trade-offs

- **Breaking list response shape** → All existing tests that assert on the flat list response must be updated. Risk is low (unit tests only, no external consumers yet).
- **ILIKE performance on large datasets** → Acceptable for this project; add `pg_trgm` index later if needed.
- **`disponible=true` filter added to public list (D-05)** → This changes observable behavior. Products currently visible with `disponible=false` will disappear from the public list. This is a correctness fix, not a regression.
- **JOIN + DISTINCT for categoria_id filter** → If a product belongs to multiple categories in the same filter, DISTINCT prevents duplicates correctly. No risk.
- **count query N+1** → The count query runs as a separate SELECT. This is two queries per list request, acceptable. Alternatively use a window function, but that adds complexity not warranted here.
