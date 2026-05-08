# input-validation-schemas Specification

## Purpose
TBD - created by archiving change backend-input-validation-sanitization. Update Purpose after archive.
## Requirements
### Requirement: Auth request schemas with validation
The system SHALL provide Pydantic v2 schemas for authentication requests that enforce email format and password strength.

#### Scenario: Valid login request accepted
- **WHEN** a client sends `POST /api/v1/auth/login` with a valid email and non-empty password
- **THEN** the schema accepts the payload and passes it to the service layer

#### Scenario: Invalid email rejected at schema level
- **WHEN** a client sends a login request with a malformed email (e.g., "not-an-email")
- **THEN** the API returns 422 Unprocessable Entity with an RFC 7807 error body indicating email validation failure

#### Scenario: Short password rejected
- **WHEN** a client sends a register request with a password shorter than 8 characters
- **THEN** the API returns 422 with a validation error on the `password` field

### Requirement: Usuario request schemas with validation
The system SHALL provide Pydantic v2 schemas for user management requests (create, update) with length and format constraints.

#### Scenario: Valid user creation accepted
- **WHEN** a client sends a create-user request with valid email, nombre (1-100 chars), and password (8-128 chars)
- **THEN** the schema accepts it

#### Scenario: Empty nombre rejected
- **WHEN** a client sends a create-user request with `nombre: ""`
- **THEN** the API returns 422 indicating `nombre` must have at least 1 character

#### Scenario: Oversized email rejected
- **WHEN** a client sends a request with an email longer than 255 characters
- **THEN** the API returns 422 indicating the field is too long

### Requirement: Producto request schemas with validation
The system SHALL provide Pydantic v2 schemas for product requests with numeric range validation.

#### Scenario: Valid product creation accepted
- **WHEN** a client sends a create-product request with nombre (1-255 chars), precio_base > 0, stock_cantidad >= 0
- **THEN** the schema accepts it

#### Scenario: Negative price rejected
- **WHEN** a client sends a product request with `precio_base: -5`
- **THEN** the API returns 422 indicating `precio_base` must be greater than 0

#### Scenario: Negative stock rejected
- **WHEN** a client sends a product request with `stock_cantidad: -1`
- **THEN** the API returns 422 indicating `stock_cantidad` must be 0 or greater

### Requirement: Categoria request schemas with validation
The system SHALL provide Pydantic v2 schemas for category requests with name constraints.

#### Scenario: Valid category creation accepted
- **WHEN** a client sends a create-category request with nombre (1-255 chars) and optional descripcion
- **THEN** the schema accepts it

#### Scenario: Blank nombre rejected
- **WHEN** a client sends a category request with `nombre: "   "` (whitespace only)
- **THEN** the API returns 422 after `.strip()` validation reveals empty string

### Requirement: Ingrediente request schemas with validation
The system SHALL provide Pydantic v2 schemas for ingredient requests.

#### Scenario: Valid ingredient creation accepted
- **WHEN** a client sends a create-ingredient request with nombre (1-255 chars) and optional es_alergeno boolean
- **THEN** the schema accepts it

### Requirement: Pedido request schemas with validation
The System SHALL provide Pydantic v2 schemas for order creation with positive quantity validation.

#### Scenario: Valid order creation accepted
- **WHEN** a client sends a create-order request with valid direccion_entrega_id, forma_pago_id, and line items with cantidad >= 1
- **THEN** the schema accepts it

#### Scenario: Zero quantity rejected
- **WHEN** a client sends an order with a line item `cantidad: 0`
- **THEN** the API returns 422 indicating `cantidad` must be at least 1

### Requirement: Direccion request schemas with validation
The system SHALL provide Pydantic v2 schemas for delivery address requests.

#### Scenario: Valid address creation accepted
- **WHEN** a client sends a create-address request with linea1 (1-255 chars), ciudad (1-100 chars), codigo_postal (4-10 chars)
- **THEN** the schema accepts it

#### Scenario: Missing required linea1 rejected
- **WHEN** a client sends an address request without `linea1`
- **THEN** the API returns 422 indicating `linea1` is required

