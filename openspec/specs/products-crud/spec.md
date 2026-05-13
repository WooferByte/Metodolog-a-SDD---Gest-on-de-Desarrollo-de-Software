## ADDED Requirements

### Requirement: List active products
The system SHALL return a paginated list of active products (eliminado_en IS NULL) ordered by nombre. Anonymous users SHALL receive only active products. Users with STOCK or ADMIN role MAY request `?incluir_eliminados=true` to receive all products including soft-deleted ones.

#### Scenario: Public list returns only active products
- **WHEN** GET /api/v1/productos is called without authentication
- **THEN** response is 200 with a list of products where eliminado_en IS NULL

#### Scenario: Admin can request deleted products
- **WHEN** GET /api/v1/productos?incluir_eliminados=true is called with a STOCK or ADMIN token
- **THEN** response is 200 with all products including those where eliminado_en IS NOT NULL

#### Scenario: Client role cannot request deleted products
- **WHEN** GET /api/v1/productos?incluir_eliminados=true is called with a CLIENT token
- **THEN** response is 403 Forbidden (RFC 7807)

### Requirement: Get product by ID
The system SHALL return a single active product by primary key. Soft-deleted products SHALL return 404 for unauthenticated or CLIENT users.

#### Scenario: Existing product returns 200
- **WHEN** GET /api/v1/productos/{id} is called with a valid product ID
- **THEN** response is 200 with the product data

#### Scenario: Non-existent product returns 404
- **WHEN** GET /api/v1/productos/{id} is called with an ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Soft-deleted product returns 404
- **WHEN** GET /api/v1/productos/{id} is called with an ID of a soft-deleted product
- **THEN** response is 404 Not Found

### Requirement: Create product
The system SHALL allow users with STOCK or ADMIN role to create a new product. precio_base MUST be > 0. stock_cantidad MUST be >= 0.

#### Scenario: Valid creation returns 201
- **WHEN** POST /api/v1/productos is called with a valid payload and STOCK or ADMIN token
- **THEN** response is 201 Created with the new product including its assigned ID

#### Scenario: Unauthenticated creation returns 401
- **WHEN** POST /api/v1/productos is called without an Authorization header
- **THEN** response is 401 Unauthorized

#### Scenario: CLIENT role returns 403
- **WHEN** POST /api/v1/productos is called with a CLIENT token
- **THEN** response is 403 Forbidden

#### Scenario: Invalid precio_base returns 422
- **WHEN** POST /api/v1/productos is called with precio_base <= 0
- **THEN** response is 422 Unprocessable Entity

### Requirement: Update product
The system SHALL allow users with STOCK or ADMIN role to fully update a product via PUT. All updatable fields are replaced.

#### Scenario: Valid update returns 200
- **WHEN** PUT /api/v1/productos/{id} is called with a valid payload and STOCK or ADMIN token
- **THEN** response is 200 with the updated product

#### Scenario: Update non-existent product returns 404
- **WHEN** PUT /api/v1/productos/{id} is called with a non-existent ID
- **THEN** response is 404 Not Found

### Requirement: Soft delete product
The system SHALL allow users with STOCK or ADMIN role to soft-delete a product by setting eliminado_en to the current timestamp. Hard delete is never performed.

#### Scenario: Valid delete returns 204
- **WHEN** DELETE /api/v1/productos/{id} is called with STOCK or ADMIN token and the product exists
- **THEN** response is 204 No Content and the product's eliminado_en is set

#### Scenario: Delete non-existent product returns 404
- **WHEN** DELETE /api/v1/productos/{id} is called with a non-existent ID
- **THEN** response is 404 Not Found

### Requirement: Update product stock
The system SHALL allow users with STOCK or ADMIN role to update only the stock_cantidad field of a product via PATCH /api/v1/productos/{id}/stock. stock_cantidad MUST be >= 0.

#### Scenario: Valid stock patch returns 200
- **WHEN** PATCH /api/v1/productos/{id}/stock is called with {"stock_cantidad": N} (N >= 0) and STOCK or ADMIN token
- **THEN** response is 200 with the updated product showing new stock_cantidad

#### Scenario: Negative stock returns 422
- **WHEN** PATCH /api/v1/productos/{id}/stock is called with stock_cantidad < 0
- **THEN** response is 422 Unprocessable Entity
