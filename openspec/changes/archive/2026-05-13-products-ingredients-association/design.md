## Context

The `ProductoIngrediente` pivot table (fields: `producto_id`, `ingrediente_id`, `es_removible`) was introduced in the schema (ERD v5) but never exposed through the API. The `products-crud-core` change provides the base CRUD for `Producto`, and `ingredients-crud-allergens` provides the CRUD for `Ingrediente`. This change adds the association layer on top of both, following the exact same architectural pattern used in `products-categories-association` (same change cycle, already archived 2026-05-13).

Current state:
- `ProductoIngrediente` model exists in `core/models.py`
- `uow.producto_ingredientes` exists but uses `BaseRepository[ProductoIngrediente]` (no pivot-specific operations)
- No service functions, no router endpoints, no schemas for ingredient associations
- `ProductoResponse` only has `categorias`, no `ingredientes` field

## Goals / Non-Goals

**Goals:**
- Expose `GET/PUT/DELETE` sub-resource endpoints at `/api/v1/productos/{id}/ingredientes`
- Enrich `ProductoResponse` with `ingredientes: list[IngredienteCompacto]` (with `es_removible`)
- Add `?excluirAlergenos=1,3,7` filter to `GET /api/v1/productos/` to exclude products containing specified allergen ingredients
- Add `ProductoIngredienteRepository` as a dedicated pivot repo (mirrors `ProductoCategoriaRepository`)
- Upgrade `uow.producto_ingredientes` property to use the new repository
- Full test coverage (≥60%) in `backend/tests/test_productos_ingredientes.py`

**Non-Goals:**
- No changes to the `Ingrediente` CRUD endpoints (already done)
- No frontend changes (those belong to `products-catalog-public`)
- No migration (table already exists)
- No support for bulk ingredient creation inline with product creation (separate concern)

## Decisions

### D-01: Dedicated `ProductoIngredienteRepository` (mirrors `ProductoCategoriaRepository`)

**Decision**: Create `ProductoIngredienteRepository` in `productos/repository.py` with methods:
- `get_ingredientes(producto_id) -> list[tuple[Ingrediente, bool]]` — returns (Ingrediente, es_removible) pairs
- `set_ingredientes(producto_id, items: list[dict]) -> None` — atomic full replace (each item: `{ingrediente_id, es_removible}`)
- `get_association(producto_id, ingrediente_id) -> ProductoIngrediente | None`
- `remove_ingrediente(producto_id, ingrediente_id) -> None`
- `list_active_excluding_alergenos(skip, limit, alergeno_ids: list[int]) -> list[Producto]` — for the excluirAlergenos filter

**Alternative considered**: Add methods directly to `ProductoRepository`. Rejected because it violates Single Responsibility — the pivot repo should own pivot operations.

**Why return `(Ingrediente, es_removible)` pairs**: The `es_removible` field lives on the pivot row, not on `Ingrediente`. We need both to build `IngredienteCompacto`.

### D-02: `excluirAlergenos` filter lives in `ProductoIngredienteRepository`, not `ProductoRepository`

**Decision**: The query that excludes products containing allergen ingredients joins `producto_ingrediente` to `ingredientes`, which is pivot logic. The method belongs in `ProductoIngredienteRepository`. The `list_active` method in `ProductoRepository` delegates to it via the service when `alergeno_ids` is non-empty.

**Alternative considered**: Add an `alergeno_ids` parameter to `ProductoRepository.list_active`. Rejected because it imports cross-domain models (`Ingrediente`, `ProductoIngrediente`) into a repo that currently only knows `Producto`.

**Implementation**: Service calls `uow.producto_ingredientes.list_active_excluding_alergenos(skip, limit, alergeno_ids)` when the param is provided; otherwise falls back to `uow.productos.list_active(skip, limit, incluir_eliminados)`.

### D-03: `PUT /ingredientes` body structure — list of `{ingrediente_id, es_removible}` objects

**Decision**: `ProductoIngredienteSetRequest` takes `ingredientes: list[IngredienteAsociacion]` where `IngredienteAsociacion = {ingrediente_id: int, es_removible: bool = False}`.

**Why not a flat list of IDs**: Unlike categories, each association carries an extra field (`es_removible`). A flat list of IDs cannot encode that information.

**Atomic replacement**: DELETE all existing `producto_ingrediente` rows for the product, then INSERT the new set — same UoW transaction. Empty list removes all associations.

### D-04: `IngredienteCompacto` schema — carries `es_removible`

```python
class IngredienteCompacto(BaseModel):
    id: int
    nombre: str
    es_alergeno: bool
    es_removible: bool  # from pivot, not from Ingrediente itself
    model_config = {"from_attributes": True}
```

`ProductoResponse` gets a new field `ingredientes: list[IngredienteCompacto] = []`.

### D-05: Route ordering — sub-resources declared before `/{producto_id}`

Per the existing router comment: sub-resource paths (`/{producto_id}/ingredientes`, etc.) MUST be declared BEFORE `/{producto_id}` to avoid FastAPI path conflict. The new ingredient endpoints follow the same declaration order as the category endpoints.

### D-06: Validation of `ingrediente_id` values in PUT (Service owns it)

The service validates each `ingrediente_id` exists and is not soft-deleted before calling the repository. Same pattern as `set_categorias_producto` in the categories change.

### D-07: `excluirAlergenos` query param format — comma-separated integer IDs

`GET /api/v1/productos/?excluirAlergenos=1,3,7` — FastAPI receives it as a `str`, the service/router splits on comma and parses to `list[int]`. The query param is optional; if absent or empty, no allergen filtering is applied.

## Risks / Trade-offs

- **[Risk] N+1 on ingredient enrichment in `list_productos`**: Fetching ingredients for each product in a list could produce N+1 queries. Mitigation: For the list endpoint `GET /api/v1/productos/`, `ProductoResponse.ingredientes` is NOT populated (to avoid N+1). Only `GET /api/v1/productos/{id}` (single product) enriches with ingredients. The list endpoint keeps `categorias: []` and `ingredientes: []` as empty defaults for now — consistent with how categories work today.
- **[Risk] `excluirAlergenos` with large ID lists**: A `NOT IN` subquery with many IDs degrades. Mitigation: Cap to 50 IDs (validated in schema). Index on `producto_ingrediente(ingrediente_id)` already created by prior migration.
- **[Trade-off] `es_removible` lives on association, not on ingredient**: This means the same ingredient can be removable in one product and not in another (e.g., cheese in a sandwich vs. cheese in a salad). This is the correct semantic per the spec.

## Migration Plan

No migration needed — `producto_ingrediente` table already exists from a prior migration. No schema changes to existing tables. The change is purely additive (new endpoints, new field in response).

## Open Questions

None — all design decisions resolved based on:
- The `products-categories-association` pattern (direct precedent)
- `docs/Integrador.txt` spec for endpoint contracts
- `docs/CHANGES.md` v3.1 description of this change
