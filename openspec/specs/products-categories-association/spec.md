## ADDED Requirements

### Requirement: List categories of a product
The system SHALL return the list of categories currently associated with a product. The endpoint SHALL be public (no authentication required). If the product does not exist or is soft-deleted, the system SHALL return 404.

#### Scenario: Product with categories returns list
- **WHEN** GET /api/v1/productos/{id}/categorias is called with a valid product ID that has associated categories
- **THEN** response is 200 with a list of CategoriaCompacta objects (id, nombre, padre_id)

#### Scenario: Product with no categories returns empty list
- **WHEN** GET /api/v1/productos/{id}/categorias is called with a valid product ID that has no categories
- **THEN** response is 200 with an empty list []

#### Scenario: Non-existent product returns 404
- **WHEN** GET /api/v1/productos/{id}/categorias is called with a product ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Soft-deleted product returns 404
- **WHEN** GET /api/v1/productos/{id}/categorias is called with the ID of a soft-deleted product
- **THEN** response is 404 Not Found

### Requirement: Replace all categories of a product (PUT full replacement)
The system SHALL allow users with ADMIN or STOCK role to atomically replace the full set of categories assigned to a product. The operation SHALL delete all existing `producto_categoria` rows for the product and insert the new set within the same UoW transaction. An empty `categoria_ids` array SHALL remove all category associations. All provided `categoria_ids` MUST reference existing, non-deleted categories; any invalid ID SHALL cause a 404.

#### Scenario: Valid replacement returns 200
- **WHEN** PUT /api/v1/productos/{id}/categorias is called with body {"categoria_ids": [1, 2]} and an ADMIN or STOCK token
- **THEN** response is 200 with the updated list of CategoriaCompacta objects

#### Scenario: Empty array removes all categories
- **WHEN** PUT /api/v1/productos/{id}/categorias is called with body {"categoria_ids": []} and an ADMIN or STOCK token
- **THEN** response is 200 with an empty list []

#### Scenario: Non-existent product returns 404
- **WHEN** PUT /api/v1/productos/{id}/categorias is called with a product ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Non-existent categoria_id returns 404
- **WHEN** PUT /api/v1/productos/{id}/categorias is called with a categoria_id that does not exist or is soft-deleted
- **THEN** response is 404 Not Found with detail indicating which ID was not found

#### Scenario: Unauthenticated request returns 401
- **WHEN** PUT /api/v1/productos/{id}/categorias is called without an Authorization header
- **THEN** response is 401 Unauthorized

#### Scenario: CLIENT role returns 403
- **WHEN** PUT /api/v1/productos/{id}/categorias is called with a CLIENT token
- **THEN** response is 403 Forbidden

### Requirement: Remove a single category from a product
The system SHALL allow users with ADMIN or STOCK role to remove a single category association from a product. If the association does not exist (the product is not linked to that category), the system SHALL return 404.

#### Scenario: Valid removal returns 204
- **WHEN** DELETE /api/v1/productos/{id}/categorias/{categoria_id} is called with a valid product-category pair and an ADMIN or STOCK token
- **THEN** response is 204 No Content and the ProductoCategoria row is deleted

#### Scenario: Association not found returns 404
- **WHEN** DELETE /api/v1/productos/{id}/categorias/{categoria_id} is called but the product is not associated with that category
- **THEN** response is 404 Not Found

#### Scenario: Non-existent product returns 404
- **WHEN** DELETE /api/v1/productos/{id}/categorias/{categoria_id} is called with a product ID that does not exist
- **THEN** response is 404 Not Found

#### Scenario: Unauthenticated request returns 401
- **WHEN** DELETE /api/v1/productos/{id}/categorias/{categoria_id} is called without an Authorization header
- **THEN** response is 401 Unauthorized

#### Scenario: CLIENT role returns 403
- **WHEN** DELETE /api/v1/productos/{id}/categorias/{categoria_id} is called with a CLIENT token
- **THEN** response is 403 Forbidden
