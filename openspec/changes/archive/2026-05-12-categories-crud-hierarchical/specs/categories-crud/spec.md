## ADDED Requirements

### Requirement: List categories (flat)
The system SHALL return a paginated flat list of all active (non-soft-deleted) categories ordered by `nombre` ascending.

#### Scenario: List returns active categories only
- **WHEN** `GET /api/v1/categorias` is requested with no auth token
- **THEN** the system returns HTTP 200 with a JSON array of `CategoriaResponse` objects (each with `id`, `nombre`, `descripcion`, `padre_id`, `creado_en`)
- **THEN** categories with `eliminado_en IS NOT NULL` are excluded from the response

#### Scenario: Pagination via skip/limit
- **WHEN** `GET /api/v1/categorias?skip=5&limit=10` is requested
- **THEN** the system returns at most 10 results starting from offset 5

---

### Requirement: Get category by ID
The system SHALL return a single category by its primary key, or 404 if not found or soft-deleted.

#### Scenario: Existing category found
- **WHEN** `GET /api/v1/categorias/{id}` is requested with a valid `id`
- **THEN** the system returns HTTP 200 with the `CategoriaResponse` for that category

#### Scenario: Category not found or deleted
- **WHEN** `GET /api/v1/categorias/{id}` is requested with an `id` that does not exist or is soft-deleted
- **THEN** the system returns HTTP 404 with RFC 7807 error body

---

### Requirement: Get full category tree
The system SHALL return a complete recursive tree of all active categories as a flat list ordered by depth then `nombre`, where each item includes a `depth` field (0 = root).

#### Scenario: Full tree returned
- **WHEN** `GET /api/v1/categorias/tree` is requested with no auth token
- **THEN** the system returns HTTP 200 with a JSON array of `CategoriaTreeItem` objects (same as `CategoriaResponse` plus `depth: int`)
- **THEN** root categories (padre_id IS NULL) have `depth = 0`
- **THEN** children have `depth = parent.depth + 1`
- **THEN** soft-deleted categories are excluded from the tree

---

### Requirement: Get subtree from a root category
The system SHALL return the recursive subtree rooted at a given category id (inclusive), as a flat list ordered by depth then `nombre`.

#### Scenario: Valid subtree returned
- **WHEN** `GET /api/v1/categorias/{id}/subtree` is requested with a valid `id`
- **THEN** the system returns HTTP 200 with the root category at `depth = 0` and all descendants in order

#### Scenario: Non-existent root id
- **WHEN** `GET /api/v1/categorias/{id}/subtree` is requested with an `id` that does not exist or is soft-deleted
- **THEN** the system returns HTTP 404

---

### Requirement: Create category
The system SHALL allow users with role `STOCK` or `ADMIN` to create a new category. Unauthenticated or lower-privilege requests MUST be rejected.

#### Scenario: Successful creation (root category)
- **WHEN** `POST /api/v1/categorias` is requested with `{"nombre": "Bebidas", "descripcion": null, "padre_id": null}` and a valid `STOCK` or `ADMIN` JWT
- **THEN** the system creates the record and returns HTTP 201 with the `CategoriaResponse` (including the new `id`)

#### Scenario: Successful creation (child category)
- **WHEN** `POST /api/v1/categorias` is requested with `{"nombre": "Bebidas Calientes", "padre_id": 1}` and a valid `STOCK` or `ADMIN` JWT, and `id=1` exists and is active
- **THEN** the system creates the record with `padre_id = 1` and returns HTTP 201

#### Scenario: Duplicate name rejected
- **WHEN** `POST /api/v1/categorias` is requested with a `nombre` that already exists in the active categories
- **THEN** the system returns HTTP 409 with an error message indicating name conflict

#### Scenario: Invalid padre_id rejected
- **WHEN** `POST /api/v1/categorias` is requested with a `padre_id` that references a non-existent or soft-deleted category
- **THEN** the system returns HTTP 422 with a validation error

#### Scenario: Unauthenticated request rejected
- **WHEN** `POST /api/v1/categorias` is requested without an Authorization header
- **THEN** the system returns HTTP 401

#### Scenario: Insufficient role rejected
- **WHEN** `POST /api/v1/categorias` is requested by a user with role `CLIENT` only
- **THEN** the system returns HTTP 403

---

### Requirement: Update category
The system SHALL allow users with role `STOCK` or `ADMIN` to update an existing category's `nombre`, `descripcion`, and/or `padre_id`. A `padre_id` update that would create a cycle MUST be rejected.

#### Scenario: Successful update
- **WHEN** `PUT /api/v1/categorias/{id}` is requested with partial or full body and valid STOCK/ADMIN JWT
- **THEN** the system updates only the provided fields and returns HTTP 200 with updated `CategoriaResponse`

#### Scenario: Cycle detection on padre_id update
- **WHEN** `PUT /api/v1/categorias/{id}` is requested setting `padre_id` to a value that would make the category its own ancestor (direct or transitive)
- **THEN** the system returns HTTP 400 with detail `"Cycle detected in category hierarchy"`

#### Scenario: Update of non-existent category
- **WHEN** `PUT /api/v1/categorias/{id}` is requested for an `id` that does not exist or is soft-deleted
- **THEN** the system returns HTTP 404

---

### Requirement: Soft-delete category
The system SHALL allow users with role `STOCK` or `ADMIN` to soft-delete a category by setting `eliminado_en`. Soft-delete MUST be rejected if the category has at least one product that is not itself soft-deleted.

#### Scenario: Successful soft-delete
- **WHEN** `DELETE /api/v1/categorias/{id}` is requested for a category with zero active products and valid STOCK/ADMIN JWT
- **THEN** the system sets `eliminado_en = now()` and returns HTTP 204 No Content

#### Scenario: Soft-delete blocked by active products
- **WHEN** `DELETE /api/v1/categorias/{id}` is requested for a category that has at least one product with `eliminado_en IS NULL` linked via `producto_categoria`
- **THEN** the system returns HTTP 409 with detail `"Cannot delete category with active products"`

#### Scenario: Delete of non-existent category
- **WHEN** `DELETE /api/v1/categorias/{id}` is requested for an `id` that does not exist or is already soft-deleted
- **THEN** the system returns HTTP 404

---

### Requirement: Cycle prevention enforced at data layer
The system SHALL guarantee that no cycle can exist in the `categorias` table's `padre_id` adjacency list through the anti-cycle validation in the service layer on every write operation that changes `padre_id`.

#### Scenario: Self-referencing padre_id rejected
- **WHEN** `PUT /api/v1/categorias/{id}` is requested with `padre_id` equal to `id`
- **THEN** the system returns HTTP 400 with detail `"Cycle detected in category hierarchy"`
