## ADDED Requirements

### Requirement: List ingredients
The system SHALL return a paginated flat list of active (non-deleted) ingredients ordered by `nombre`. An optional `es_alergeno` query parameter SHALL filter by allergen status when provided.

#### Scenario: List all ingredients (no filter)
- **WHEN** `GET /api/v1/ingredientes/` is requested without `es_alergeno` parameter
- **THEN** system returns HTTP 200 with a JSON array of all active ingredients

#### Scenario: Filter by allergen status true
- **WHEN** `GET /api/v1/ingredientes/?es_alergeno=true` is requested
- **THEN** system returns HTTP 200 with only ingredients where `es_alergeno = true`

#### Scenario: Filter by allergen status false
- **WHEN** `GET /api/v1/ingredientes/?es_alergeno=false` is requested
- **THEN** system returns HTTP 200 with only ingredients where `es_alergeno = false`

#### Scenario: List is public (no auth required)
- **WHEN** `GET /api/v1/ingredientes/` is requested without Authorization header
- **THEN** system returns HTTP 200 (no authentication required)

---

### Requirement: Get ingredient by ID
The system SHALL return a single ingredient by its primary key or 404 if not found or soft-deleted.

#### Scenario: Get existing ingredient
- **WHEN** `GET /api/v1/ingredientes/{id}` is requested with a valid ID
- **THEN** system returns HTTP 200 with the ingredient data

#### Scenario: Get non-existent ingredient
- **WHEN** `GET /api/v1/ingredientes/{id}` is requested with an ID that does not exist
- **THEN** system returns HTTP 404 with RFC 7807 error body

#### Scenario: Get is public
- **WHEN** `GET /api/v1/ingredientes/{id}` is requested without Authorization header
- **THEN** system returns HTTP 200 or 404 (no authentication required)

---

### Requirement: Create ingredient
The system SHALL create a new ingredient. `nombre` MUST be unique across non-deleted ingredients. `es_alergeno` is required (no default — caller must specify). Requires STOCK or ADMIN role.

#### Scenario: Successful creation
- **WHEN** `POST /api/v1/ingredientes/` is requested with valid `nombre` and `es_alergeno`
- **THEN** system returns HTTP 201 with the created ingredient including its `id` and `creado_en`

#### Scenario: Duplicate nombre
- **WHEN** `POST /api/v1/ingredientes/` is requested with a `nombre` that already exists (active or soft-deleted)
- **THEN** system returns HTTP 409 with RFC 7807 error body

#### Scenario: Create requires STOCK or ADMIN role
- **WHEN** `POST /api/v1/ingredientes/` is requested with a CLIENT role token
- **THEN** system returns HTTP 403

#### Scenario: Create requires authentication
- **WHEN** `POST /api/v1/ingredientes/` is requested without Authorization header
- **THEN** system returns HTTP 401

---

### Requirement: Update ingredient
The system SHALL partially update an existing ingredient. Only provided fields are modified. `nombre` uniqueness constraint applies. Requires STOCK or ADMIN role.

#### Scenario: Successful update
- **WHEN** `PUT /api/v1/ingredientes/{id}` is requested with valid update data
- **THEN** system returns HTTP 200 with updated ingredient data

#### Scenario: Update non-existent ingredient
- **WHEN** `PUT /api/v1/ingredientes/{id}` is requested with a non-existent ID
- **THEN** system returns HTTP 404

#### Scenario: Update with duplicate nombre
- **WHEN** `PUT /api/v1/ingredientes/{id}` is requested with a `nombre` that belongs to another ingredient
- **THEN** system returns HTTP 409

#### Scenario: Update requires STOCK or ADMIN role
- **WHEN** `PUT /api/v1/ingredientes/{id}` is requested with a CLIENT role token
- **THEN** system returns HTTP 403

---

### Requirement: Soft-delete ingredient
The system SHALL soft-delete an ingredient (set `eliminado_en`). Deletion MUST be rejected if the ingredient is linked to any active product. Requires STOCK or ADMIN role.

#### Scenario: Successful soft-delete
- **WHEN** `DELETE /api/v1/ingredientes/{id}` is requested for an ingredient with no active products
- **THEN** system sets `eliminado_en` and returns HTTP 204

#### Scenario: Delete blocked by active products
- **WHEN** `DELETE /api/v1/ingredientes/{id}` is requested for an ingredient linked to active products
- **THEN** system returns HTTP 409 with RFC 7807 error body

#### Scenario: Delete non-existent ingredient
- **WHEN** `DELETE /api/v1/ingredientes/{id}` is requested with a non-existent ID
- **THEN** system returns HTTP 404

#### Scenario: Delete requires STOCK or ADMIN role
- **WHEN** `DELETE /api/v1/ingredientes/{id}` is requested without Authorization header
- **THEN** system returns HTTP 401
