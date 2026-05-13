## ADDED Requirements

### Requirement: Text search on public product list
The system SHALL support a `?q=` query parameter on `GET /api/v1/productos` that performs a case-insensitive ILIKE search on `nombre` and `descripcion` columns. The search SHALL be optional; omitting `?q=` returns all active products. The search SHALL be applied before pagination. Special characters in `q` SHALL be treated as literal characters (no SQL injection risk; use parameterized queries).

#### Scenario: Search by nombre returns matching products
- **WHEN** GET /api/v1/productos?q=pizza is called
- **THEN** response is 200 with items whose nombre or descripcion contains "pizza" (case-insensitive)

#### Scenario: Search with no matches returns empty items list
- **WHEN** GET /api/v1/productos?q=xyznonexistent is called
- **THEN** response is 200 with items=[] and total=0

#### Scenario: Search is case-insensitive
- **WHEN** GET /api/v1/productos?q=PIZZA is called and a product named "Pizza Margarita" exists
- **THEN** response is 200 with the product included in items

#### Scenario: Omitting q returns all active products
- **WHEN** GET /api/v1/productos is called without ?q=
- **THEN** response is 200 with all active products (no text filter applied)

### Requirement: Category filter on public product list
The system SHALL support a `?categoria_id=` integer query parameter on `GET /api/v1/productos` that filters products belonging to the specified category via the `producto_categoria` pivot table. Products not associated with that category SHALL be excluded. The filter SHALL be optional.

#### Scenario: Filter by valid categoria_id returns only products in that category
- **WHEN** GET /api/v1/productos?categoria_id=3 is called
- **THEN** response is 200 with items containing only products associated with categoria 3

#### Scenario: Filter by categoria_id with no matches returns empty list
- **WHEN** GET /api/v1/productos?categoria_id=9999 is called and no products belong to that category
- **THEN** response is 200 with items=[] and total=0

#### Scenario: Non-integer categoria_id returns 422
- **WHEN** GET /api/v1/productos?categoria_id=abc is called
- **THEN** response is 422 Unprocessable Entity

#### Scenario: Omitting categoria_id returns all active products
- **WHEN** GET /api/v1/productos is called without ?categoria_id=
- **THEN** response is 200 with all active products (no category filter applied)

### Requirement: Combined search and category filter
The system SHALL support combining `?q=` and `?categoria_id=` filters in the same request. Both filters SHALL be applied simultaneously (AND logic).

#### Scenario: Combined q and categoria_id returns intersection
- **WHEN** GET /api/v1/productos?q=pizza&categoria_id=2 is called
- **THEN** response is 200 with only products that match the text "pizza" AND belong to category 2

### Requirement: Paginated response envelope for product list
The `GET /api/v1/productos` endpoint SHALL return a paginated envelope instead of a flat list. The envelope SHALL have the shape: `{ "items": [...], "total": N, "page": P, "size": S, "pages": T }`. The endpoint SHALL accept `?page=` (1-based, default=1) and `?size=` (default=20, max=100) as canonical pagination parameters. The existing `?skip=` and `?limit=` parameters SHALL remain supported for backward compatibility.

#### Scenario: Default pagination returns first page with envelope
- **WHEN** GET /api/v1/productos is called without pagination params
- **THEN** response is 200 with shape { items: [...], total: N, page: 1, size: 20, pages: P }

#### Scenario: Explicit page and size pagination
- **WHEN** GET /api/v1/productos?page=2&size=5 is called and total=12 products exist
- **THEN** response is 200 with page=2, size=5, total=12, pages=3, items contains products 6-10

#### Scenario: Total reflects filtered count not raw count
- **WHEN** GET /api/v1/productos?q=pizza is called and 3 products match
- **THEN** response total=3 and pages=1 (with default size=20)

### Requirement: Public list excludes non-available products
The `GET /api/v1/productos` endpoint WITHOUT `?incluir_eliminados=true` SHALL filter `WHERE disponible = true AND eliminado_en IS NULL`. Products with `disponible=false` SHALL NOT appear in the public catalog.

#### Scenario: Product with disponible=false is excluded from public list
- **WHEN** GET /api/v1/productos is called without authentication
- **THEN** products with disponible=false are NOT present in items

#### Scenario: Product with disponible=true is included in public list
- **WHEN** GET /api/v1/productos is called without authentication
- **THEN** products with disponible=true and eliminado_en IS NULL ARE present in items
