## Context

The `Categoria` SQLModel entity already exists in `backend/core/models.py` with fields: `id`, `nombre` (unique, max 255), `descripcion`, `padre_id` (FK to self, nullable), `creado_en`, `actualizado_en`, `eliminado_en` (soft delete). The `categorias` table was created in migration 001 and the `UnitOfWork` already exposes `uow.categorias` as `BaseRepository[Categoria]`.

The `backend/categorias/` directory already contains `schemas.py` with `CategoriaCreate`, `CategoriaUpdate`, and `CategoriaResponse`. The schemas use Pydantic v2 `field_validator` for XSS sanitization and strip whitespace.

The project follows a strict unidirectional layer pattern: `Router → Service → UoW → Repository → Model`. The `BaseRepository[Categoria]` provides generic CRUD. For the hierarchical CTE query, we need a dedicated `CategoriaRepository` that extends `BaseRepository` with tree-specific methods.

RBAC guards (`require_role`) are deployed and working from the `route-protection-rbac` change. `infrastructure/dependencies.py` exposes `get_current_user` and `require_role`.

## Goals / Non-Goals

**Goals:**
- Implement all 5 REST endpoints at `/api/v1/categorias` following project conventions
- CTE recursive query to return the full tree (or subtree from a given root) as a flat list ordered by depth
- Anti-cycle guard on create/update: reject `padre_id` that would create a cycle (A→B→A or deeper)
- Active-products guard on delete: reject soft-delete if category has at least one product with `eliminado_en IS NULL` in `producto_categoria`
- Soft delete with `eliminado_en` (no hard delete)
- Public GET endpoints; POST/PUT/DELETE require `STOCK` or `ADMIN` role
- Migration for `padre_id` index to support CTE join performance
- Tests in `backend/tests/test_categorias.py` (service unit tests + router integration tests)

**Non-Goals:**
- Frontend implementation (deferred to a future change)
- Pagination on the tree endpoint (returned as a full flat list — category count is bounded)
- Bulk import / CSV upload
- Reordering categories within the same level

## Decisions

### Decision 1: Dedicated `CategoriaRepository` extends `BaseRepository`

**Choice**: Create `backend/categorias/repository.py` with `CategoriaRepository(BaseRepository[Categoria])` that adds `get_tree(root_id=None)` and `has_active_products(categoria_id)` methods that execute raw SQLAlchemy `text()` queries for the CTE and product check.

**Alternative considered**: Put CTE logic in `service.py` via `uow.session.execute(text(...))` directly. Rejected because it breaks the layer boundary — services should not reach into the session directly; that is the repository's job.

**Rationale**: Keeps the layer contract intact. `UnitOfWork` will expose `categorias` as a `CategoriaRepository` instance (not bare `BaseRepository`) by overriding the property.

### Decision 2: CTE approach for tree query

**Choice**: PostgreSQL recursive CTE using SQLAlchemy `text()`.

```sql
WITH RECURSIVE arbol AS (
    -- anchor: category with padre_id IS NULL (or = root_id)
    SELECT id, nombre, descripcion, padre_id, creado_en, actualizado_en, 0 AS depth
    FROM categorias
    WHERE eliminado_en IS NULL
      AND padre_id IS NULL  -- or: AND id = :root_id
    UNION ALL
    SELECT c.id, c.nombre, c.descripcion, c.padre_id, c.creado_en, c.actualizado_en, a.depth + 1
    FROM categorias c
    JOIN arbol a ON c.padre_id = a.id
    WHERE c.eliminado_en IS NULL
)
SELECT * FROM arbol ORDER BY depth, nombre;
```

When `root_id` is provided: anchor changes to `WHERE id = :root_id` and the result includes the root itself plus all descendants.

**Alternative considered**: Storing `path` as `ltree` extension. Rejected — requires enabling `ltree` extension in PostgreSQL and adds complexity. CTE is fully supported with native PostgreSQL and asyncpg.

**Rationale**: CTE is the canonical recursive pattern for adjacency-list hierarchies in PostgreSQL. It is efficient for trees with bounded depth (food categories don't exceed ~5 levels).

### Decision 3: Anti-cycle validation in service layer

**Choice**: On `create_categoria` and `update_categoria`, if `padre_id` is provided, walk the ancestor chain of `padre_id` to check whether the current category's `id` appears. If it does, raise `HTTPException(400, "Cycle detected")`.

**Algorithm**:
```python
async def _would_create_cycle(uow, child_id: int, proposed_padre_id: int) -> bool:
    # Walk ancestors of proposed_padre_id
    current_id = proposed_padre_id
    visited = set()
    while current_id is not None:
        if current_id == child_id:
            return True  # cycle found
        if current_id in visited:
            break  # guard against existing cycles in data
        visited.add(current_id)
        ancestor = await uow.categorias.get_by_id(current_id)
        if ancestor is None:
            break
        current_id = ancestor.padre_id
    return False
```

On create, `child_id` is not yet known — skip cycle check (a new category has no children yet, so it cannot form a cycle at creation time). On update, if `padre_id` changes, run the check with the existing category's `id`.

**Alternative considered**: CTE-based cycle check in DB. More efficient for deep trees but adds query complexity. Given category trees are shallow (≤5 levels), the iterative walk is acceptable and simpler to test.

### Decision 4: `CategoriaTreeItem` response schema for tree endpoint

**Choice**: Add a `CategoriaTreeItem` schema extending `CategoriaResponse` with a `depth: int` field. The tree endpoint returns `List[CategoriaTreeItem]`.

**Rationale**: Consumers (frontend catalog) need `depth` to render indentation without re-computing the tree client-side.

### Decision 5: Endpoint structure

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/categorias` | Public | List flat (no tree), paginated, exclude soft-deleted |
| GET | `/api/v1/categorias/tree` | Public | Full recursive tree (flat list with depth field) |
| GET | `/api/v1/categorias/{id}` | Public | Single category |
| GET | `/api/v1/categorias/{id}/subtree` | Public | Subtree rooted at `id` |
| POST | `/api/v1/categorias` | STOCK or ADMIN | Create category |
| PUT | `/api/v1/categorias/{id}` | STOCK or ADMIN | Full/partial update |
| DELETE | `/api/v1/categorias/{id}` | STOCK or ADMIN | Soft delete (guarded) |

**Why GET /tree and GET /{id}/subtree as separate endpoints**: Keeps the flat list endpoint cheap (no CTE) for admin pagination while providing a dedicated tree endpoint for catalog use.

### Decision 6: `UnitOfWork` override for `CategoriaRepository`

**Choice**: Override `uow.categorias` property in `infrastructure/uow.py` to return `CategoriaRepository(self.session)` instead of `BaseRepository[Categoria](self.session, Categoria)`. This makes the CTE methods available through the standard UoW interface without changing the DI signature.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Infinite loop in ancestor walk if existing data already has a cycle | Guard with `visited` set in `_would_create_cycle` — breaks on first revisited node |
| CTE performance degrades with large number of categories | Index on `padre_id` (migration 006) accelerates the recursive join. Category count is bounded for a food store (~100 max) |
| `nombre` uniqueness constraint — SQLAlchemy IntegrityError on duplicate | Catch `IntegrityError` in service, re-raise as `HTTPException(409)` |
| Deleting a parent that has soft-deleted children orphans them logically | Soft-deleting a parent does NOT cascade to children — children become root-less but remain in DB. This is acceptable for a food store; a future change can add cascade logic if needed |

## Migration Plan

1. Migration 006 adds `CREATE INDEX idx_categorias_padre_id ON categorias (padre_id) WHERE eliminado_en IS NULL` — additive, no downtime, no data transformation
2. `alembic upgrade head` — runs in seconds, no lock on existing data
3. Rollback: `alembic downgrade -1` drops the index

## Open Questions

- None — all decisions have been made based on existing codebase patterns and spec requirements.
