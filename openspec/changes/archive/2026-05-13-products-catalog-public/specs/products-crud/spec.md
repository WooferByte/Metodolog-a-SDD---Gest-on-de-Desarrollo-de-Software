## MODIFIED Requirements

### Requirement: List active products
The system SHALL return a paginated envelope `{ "items": list[ProductoResponse], "total": int, "page": int, "size": int, "pages": int }` for `GET /api/v1/productos`. The endpoint SHALL accept `?page=` (1-based integer, default=1) and `?size=` (integer, default=20, max=100) as the canonical pagination parameters. The existing `?skip=` and `?limit=` parameters SHALL remain supported. The public list (without `?incluir_eliminados=true`) SHALL filter `WHERE disponible = true AND eliminado_en IS NULL`. Users with STOCK or ADMIN role MAY request `?incluir_eliminados=true` to receive all products. The endpoint SHALL additionally accept `?q=` (ILIKE text search on nombre/descripcion) and `?categoria_id=` (integer, filter by category association). All filters are combined with AND logic.

#### Scenario: Public list returns only active available products
- **WHEN** GET /api/v1/productos is called without authentication
- **THEN** response is 200 with paginated envelope where all items have eliminado_en IS NULL and disponible=true

#### Scenario: Admin can request deleted products
- **WHEN** GET /api/v1/productos?incluir_eliminados=true is called with a STOCK or ADMIN token
- **THEN** response is 200 with paginated envelope containing all products including soft-deleted ones

#### Scenario: Client role cannot request deleted products
- **WHEN** GET /api/v1/productos?incluir_eliminados=true is called with a CLIENT token
- **THEN** response is 403 Forbidden (RFC 7807)
