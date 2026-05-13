## MODIFIED Requirements

### Requirement: Get product by ID
The system SHALL return a single active product by primary key. Soft-deleted products SHALL return 404 for unauthenticated or CLIENT users. The response SHALL include a `categorias` field containing the list of categories (id, nombre, padre_id) currently associated with the product. If the product has no categories, `categorias` SHALL be an empty list.

#### Scenario: Existing product returns 200
- **WHEN** GET /api/v1/productos/{id} is called with a valid product ID
- **THEN** response is 200 with the product data including a `categorias` field (list, may be empty)

#### Scenario: Non-existent product returns 404
- **WHEN** GET /api/v1/productos/{id} is called with an ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Soft-deleted product returns 404
- **WHEN** GET /api/v1/productos/{id} is called with an ID of a soft-deleted product
- **THEN** response is 404 Not Found

#### Scenario: Product detail includes assigned categories
- **WHEN** GET /api/v1/productos/{id} is called for a product that belongs to categories [1, 3]
- **THEN** response is 200 and the `categorias` array contains objects with id, nombre, and padre_id for categories 1 and 3
