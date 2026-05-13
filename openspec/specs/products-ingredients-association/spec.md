## ADDED Requirements

### Requirement: List ingredients of a product
The system SHALL return the list of ingredients currently associated with a product, including the `es_removible` flag per association. The endpoint SHALL be public (no authentication required). If the product does not exist or is soft-deleted, the system SHALL return 404.

#### Scenario: Product with ingredients returns list
- **WHEN** GET /api/v1/productos/{id}/ingredientes is called with a valid product ID that has associated ingredients
- **THEN** response is 200 with a list of IngredienteCompacto objects (id, nombre, es_alergeno, es_removible)

#### Scenario: Product with no ingredients returns empty list
- **WHEN** GET /api/v1/productos/{id}/ingredientes is called with a valid product ID that has no ingredient associations
- **THEN** response is 200 with an empty list []

#### Scenario: Non-existent product returns 404
- **WHEN** GET /api/v1/productos/{id}/ingredientes is called with a product ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Soft-deleted product returns 404
- **WHEN** GET /api/v1/productos/{id}/ingredientes is called with the ID of a soft-deleted product
- **THEN** response is 404 Not Found

### Requirement: Replace all ingredients of a product (PUT full replacement)
The system SHALL allow users with ADMIN or STOCK role to atomically replace the full set of ingredients assigned to a product. The operation SHALL delete all existing `producto_ingrediente` rows for the product and insert the new set within the same UoW transaction. An empty `ingredientes` array SHALL remove all ingredient associations. Each entry in the request body MUST specify `ingrediente_id` and optionally `es_removible` (defaults to false). All provided `ingrediente_id` values MUST reference existing, non-deleted ingredients; any invalid ID SHALL cause a 404.

#### Scenario: Valid replacement returns 200 with updated list
- **WHEN** PUT /api/v1/productos/{id}/ingredientes is called with body {"ingredientes": [{"ingrediente_id": 1, "es_removible": true}, {"ingrediente_id": 2, "es_removible": false}]} and an ADMIN or STOCK token
- **THEN** response is 200 with the updated list of IngredienteCompacto objects

#### Scenario: Empty array removes all ingredient associations
- **WHEN** PUT /api/v1/productos/{id}/ingredientes is called with body {"ingredientes": []} and an ADMIN or STOCK token
- **THEN** response is 200 with an empty list []

#### Scenario: Non-existent product returns 404
- **WHEN** PUT /api/v1/productos/{id}/ingredientes is called with a product ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Non-existent ingrediente_id returns 404
- **WHEN** PUT /api/v1/productos/{id}/ingredientes is called with an ingrediente_id that does not exist or is soft-deleted
- **THEN** response is 404 Not Found with detail indicating which ID was not found

#### Scenario: Unauthenticated request returns 401
- **WHEN** PUT /api/v1/productos/{id}/ingredientes is called without an Authorization header
- **THEN** response is 401 Unauthorized

#### Scenario: CLIENT role returns 403
- **WHEN** PUT /api/v1/productos/{id}/ingredientes is called with a CLIENT token
- **THEN** response is 403 Forbidden

### Requirement: Remove a single ingredient from a product
The system SHALL allow users with ADMIN or STOCK role to remove a single ingredient association from a product. If the association does not exist (the product is not linked to that ingredient), the system SHALL return 404.

#### Scenario: Valid removal returns 204
- **WHEN** DELETE /api/v1/productos/{id}/ingredientes/{ing_id} is called with a valid product-ingredient pair and an ADMIN or STOCK token
- **THEN** response is 204 No Content and the ProductoIngrediente row is deleted

#### Scenario: Association not found returns 404
- **WHEN** DELETE /api/v1/productos/{id}/ingredientes/{ing_id} is called but the product is not associated with that ingredient
- **THEN** response is 404 Not Found

#### Scenario: Non-existent product returns 404
- **WHEN** DELETE /api/v1/productos/{id}/ingredientes/{ing_id} is called with a product ID that does not exist
- **THEN** response is 404 Not Found

#### Scenario: Unauthenticated request returns 401
- **WHEN** DELETE /api/v1/productos/{id}/ingredientes/{ing_id} is called without an Authorization header
- **THEN** response is 401 Unauthorized

#### Scenario: CLIENT role returns 403
- **WHEN** DELETE /api/v1/productos/{id}/ingredientes/{ing_id} is called with a CLIENT token
- **THEN** response is 403 Forbidden

### Requirement: Filter product listing by allergen exclusion
The system SHALL allow the product listing endpoint to accept an optional `excluirAlergenos` query parameter containing a comma-separated list of ingredient IDs that are allergens. Products that contain ANY of the listed allergen ingredients in their `producto_ingrediente` associations SHALL be excluded from the result. The parameter SHALL be optional; if absent or empty, no allergen filtering is applied. The parameter SHALL accept up to 50 IDs; exceeding this limit SHALL return 422.

#### Scenario: Listing with excluirAlergenos excludes matching products
- **WHEN** GET /api/v1/productos/?excluirAlergenos=1,3 is called and products P1 and P2 contain ingredient 1, product P3 does not
- **THEN** response is 200 with a list that includes P3 but excludes P1 and P2

#### Scenario: Listing without excluirAlergenos returns all active products
- **WHEN** GET /api/v1/productos/ is called without the excluirAlergenos parameter
- **THEN** response is 200 with all active (non-deleted) products regardless of ingredients

#### Scenario: excluirAlergenos with empty value is ignored
- **WHEN** GET /api/v1/productos/?excluirAlergenos= is called
- **THEN** response is 200 with all active products (no allergen filtering applied)

#### Scenario: excluirAlergenos with invalid non-integer value returns 422
- **WHEN** GET /api/v1/productos/?excluirAlergenos=abc is called
- **THEN** response is 422 Unprocessable Entity

#### Scenario: excluirAlergenos with more than 50 IDs returns 422
- **WHEN** GET /api/v1/productos/?excluirAlergenos=1,2,3,...,51 (51 IDs) is called
- **THEN** response is 422 Unprocessable Entity
