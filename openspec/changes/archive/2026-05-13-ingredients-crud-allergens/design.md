## Context

The `Ingrediente` SQLModel table already exists in `backend/core/models.py` with fields `id`, `nombre` (UNIQUE), `es_alergeno`, `creado_en`, `eliminado_en`. The `ProductoIngrediente` pivot table (N:M) also exists. The `IngredienteCreate` / `IngredienteUpdate` / `IngredienteResponse` schemas are already defined in `backend/ingredientes/schemas.py`. The UoW already exposes `uow.ingredientes` but it is wired to the generic `BaseRepository[Ingrediente]`, which lacks an `has_active_products()` guard and a list-by-allergen query.

The categorias module (`backend/categorias/`) is the canonical reference for this change: same layer structure, same test strategy, same router pattern.

## Goals / Non-Goals

**Goals:**
- Implement `IngredienteRepository` extending `BaseRepository[Ingrediente]` with `has_active_products()` and `list_by_alergeno()` methods
- Implement `IngredienteService` with all business logic (404 guards, UNIQUE → 409, active-products guard on delete)
- Implement `IngredienteRouter` with `response_model` on every endpoint and `require_role` guards
- Update `UnitOfWork.ingredientes` property to return `IngredienteRepository` instead of `BaseRepository[Ingrediente]`
- Write Alembic migration `007_add_ingredientes_index.py` (partial index on `ingredientes.nombre WHERE eliminado_en IS NULL`)
- Write unit tests covering service business logic and router auth requirements

**Non-Goals:**
- Frontend UI for ingredient management (separate change)
- Product-ingredient assignment UI
- Bulk import/export of ingredients

## Decisions

### D1: Extend BaseRepository — not rewrite

**Decision**: `IngredienteRepository(BaseRepository[Ingrediente])` adds only the two methods that require custom SQL (`has_active_products`, `list_by_alergeno`). All generic CRUD (create, get_by_id, list_all, update, soft_delete) is inherited from `BaseRepository`.

**Rationale**: Mirrors the exact pattern established by `CategoriaRepository`. Keeps custom code minimal and consistent.

**Alternative considered**: Standalone repository with full CRUD re-implementation — rejected because it duplicates code and drifts from project conventions.

---

### D2: Filter endpoint `GET /api/v1/ingredientes?es_alergeno=true/false`

**Decision**: Optional query parameter `es_alergeno: Optional[bool] = None`. When `None`, returns all ingredients (existing `list_all` behavior). When `True` or `False`, delegates to `list_by_alergeno(es_alergeno)`.

**Rationale**: Simple, stateless, matches the spec. Does not require cursor pagination (ingredient lists are small).

**Alternative considered**: Separate `GET /api/v1/ingredientes/alergenos` endpoint — rejected because filtering via query param is the REST convention established in the api-design skill.

---

### D3: Active-products guard uses ProductoIngrediente JOIN

**Decision**: `has_active_products(ingrediente_id)` runs an EXISTS-style SQL with `LIMIT 1` joining `producto_ingrediente` to `productos` filtering `productos.eliminado_en IS NULL`.

**Rationale**: Exact same pattern as `CategoriaRepository.has_active_products()` which joins `producto_categoria`. Consistent and efficient.

---

### D4: Migration adds partial index on `ingredientes.nombre`

**Decision**: Add `idx_ingredientes_nombre_active` — a partial B-tree index on `nombre WHERE eliminado_en IS NULL`.

**Rationale**: The UNIQUE constraint on `nombre` already exists from the initial migration, so this index is an optimization for lookup queries on active records, following the same pattern as migration 006.

## Risks / Trade-offs

- **[Risk] `uow.ingredientes` type annotation change** → The UoW property return type changes from `BaseRepository[Ingrediente]` to `IngredienteRepository`. Any existing code calling `uow.ingredientes` will still work (duck-typing compatible), but type checkers will see the narrower type. Mitigation: add explicit type annotation `-> IngredienteRepository`.

- **[Risk] Alembic migration chain** → Must set `down_revision = "006_add_categoria_padre_id_index"`. If migration 006 is not at head, `upgrade head` will fail. Mitigation: verify `alembic current` shows `006` at head before running migration.

- **[Trade-off] `list_by_alergeno` custom method vs. generic `find_all_by`** → `BaseRepository.find_all_by(es_alergeno=True)` would work, but it doesn't guarantee consistent ordering. `list_by_alergeno` can enforce `ORDER BY nombre` and respect the `skip/limit` pagination contract. Decision: implement the explicit method.

## Migration Plan

1. Create `backend/alembic/versions/007_add_ingredientes_index.py` with `down_revision = "006_add_categoria_padre_id_index"`
2. Run `alembic upgrade head` — adds partial index, no data changes
3. Rollback: `alembic downgrade -1` drops the index; safe at any time

## Open Questions

None — requirements are fully specified in `docs/Integrador.txt` and the existing model + schemas confirm the field set.
