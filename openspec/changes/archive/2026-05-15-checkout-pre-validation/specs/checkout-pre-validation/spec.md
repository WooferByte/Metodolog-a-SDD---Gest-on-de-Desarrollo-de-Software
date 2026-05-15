## ADDED Requirements

### Requirement: Validation endpoint accepts cart contents and returns structured report

The system SHALL expose `POST /api/v1/pedidos/validar` (requires authenticated CLIENT role) that accepts a list of cart items with their product IDs, quantities, and cart-stored prices, plus the ID of the selected delivery address, and returns a `ValidarCarritoResponse` with four diagnostic fields.

#### Scenario: All validations pass

- **WHEN** the request contains at least one item, all products exist and are available, all stock quantities are sufficient, all prices match within 0.01 tolerance, and the address ID belongs to the authenticated user
- **THEN** the endpoint returns HTTP 200 with `stockInsuficiente=[]`, `productosInvalidos=[]`, `cambiosDePrecio=[]`, `carritoVacio=false`, `sinDireccion=false`

#### Scenario: Empty cart submitted

- **WHEN** the request contains an empty `items` array
- **THEN** the endpoint returns HTTP 422 with RFC 7807 body (`type`, `title`, `status`, `detail`, `instance`) and `carritoVacio=true` in the detail context

#### Scenario: User has no delivery addresses

- **WHEN** the authenticated user has zero non-soft-deleted addresses in `direcciones_entrega`
- **THEN** the endpoint returns HTTP 422 with RFC 7807 body and `sinDireccion=true` in the detail context

#### Scenario: Cart has both empty and no-address violations simultaneously

- **WHEN** both `carritoVacio` and `sinDireccion` conditions are true
- **THEN** the endpoint returns HTTP 422 with RFC 7807 body that describes both violations

#### Scenario: Insufficient stock detected

- **WHEN** a cart item requests quantity greater than `producto.stock`
- **THEN** the endpoint returns HTTP 200 with that product appearing in `stockInsuficiente` array containing `{ producto_id, nombre, stockActual, cantidadSolicitada }` and the `productosInvalidos` array does NOT include it (stock shortage is not the same as an invalid product)

#### Scenario: Price drift detected

- **WHEN** a cart item's `precio_carrito` differs from the product's current `precio` by more than 0.01
- **THEN** the endpoint returns HTTP 200 with that product appearing in `cambiosDePrecio` array containing `{ producto_id, precioCarrito, precioActual }`

#### Scenario: Product no longer available

- **WHEN** a cart item references a product with `disponible=false` or `eliminado_en IS NOT NULL`
- **THEN** the endpoint returns HTTP 200 with that product's ID in `productosInvalidos` array

#### Scenario: Product does not exist

- **WHEN** a cart item references a `producto_id` that has no matching row in the database
- **THEN** the endpoint returns HTTP 200 with that `producto_id` in `productosInvalidos` array

### Requirement: Validation endpoint is read-only and idempotent

The validation endpoint SHALL NOT modify any database state. Repeated calls with identical inputs SHALL return identical outputs (given no external state changes).

#### Scenario: Validation does not decrement stock

- **WHEN** the endpoint is called with a valid cart
- **THEN** product stock values remain unchanged in the database

#### Scenario: Identical requests return identical results

- **WHEN** the same request body is sent twice in succession without any DB changes between calls
- **THEN** both responses are identical

### Requirement: Backend performs batch product lookup in single query

The validation service SHALL fetch all products referenced in the cart using a single `SELECT ... WHERE id IN (...)` query rather than N individual lookups.

#### Scenario: Batch query used for N items

- **WHEN** the cart contains 5 distinct products
- **THEN** only 1 SQL SELECT query is issued against the `productos` table for the product data retrieval step

### Requirement: Validation requires CLIENT authentication

The validation endpoint SHALL require a valid JWT access token with role CLIENT (role_id=4). Unauthenticated or unauthorized requests SHALL be rejected.

#### Scenario: Unauthenticated request rejected

- **WHEN** a request is sent to `POST /api/v1/pedidos/validar` without an Authorization header
- **THEN** the endpoint returns HTTP 401

#### Scenario: Non-CLIENT role rejected

- **WHEN** a request is sent by a user with ADMIN role
- **THEN** the endpoint returns HTTP 403
