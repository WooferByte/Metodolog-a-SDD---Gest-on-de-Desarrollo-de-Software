# route-protection Specification

## Purpose
FastAPI RBAC dependency layer. `require_role(roles)` factory enforces role membership on protected endpoints, returning 401 on missing/invalid token and 403 on insufficient role.

## Requirements

### Requirement: require_role factory enforces role membership
The system SHALL expose a `require_role(roles: list[str])` factory in `backend/core/dependencies.py` that returns a FastAPI-compatible dependency. The returned dependency SHALL read the authenticated user from `get_current_user` and verify that at least one of the user's roles matches the allowed list.

#### Scenario: Valid token with matching role is allowed
- **WHEN** a request carries a valid JWT and the user has a role in the allowed list
- **THEN** the request proceeds to the endpoint handler with HTTP 2xx

#### Scenario: Valid token with no matching role returns 403
- **WHEN** a request carries a valid JWT but the user's roles do not include any role in the allowed list
- **THEN** the system returns HTTP 403 with RFC 7807 body `{"type": "about:blank", "title": "Forbidden", "status": 403, "detail": "No tenés el rol requerido"}`

#### Scenario: Missing or invalid token returns 401
- **WHEN** a request has no Authorization header or an invalid/expired token
- **THEN** the system returns HTTP 401 with RFC 7807 body `{"type": "about:blank", "title": "Unauthorized", "status": 401, "detail": "Token requerido"}`

### Requirement: Public endpoints require no authentication
The system SHALL allow the following endpoints to be called without any Authorization header: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/productos`, `GET /api/v1/productos/{id}`, `GET /api/v1/categorias`.

#### Scenario: Public endpoint called without token succeeds
- **WHEN** a client calls a public endpoint with no Authorization header
- **THEN** the system returns HTTP 2xx (or the expected response for that endpoint)

### Requirement: Role-endpoint mapping is explicit and complete
Each protected endpoint SHALL declare its required roles via `dependencies=[Depends(require_role([...]))]`. The mapping SHALL be:

| Endpoint group | Required roles |
|---|---|
| `POST /auth/logout` | any authenticated user |
| `GET /perfil`, `PUT /perfil`, `POST /perfil/cambiar-password` | CLIENT |
| `GET/POST/PUT/DELETE /direcciones` | CLIENT |
| `POST /pedidos`, `GET /pedidos`, `GET /pedidos/{id}` | CLIENT |
| `POST/PUT/PATCH/DELETE /categorias` | ADMIN, STOCK |
| `POST/PUT/PATCH/DELETE /productos` | ADMIN, STOCK |
| `POST/PUT/DELETE /ingredientes` | ADMIN, STOCK |
| `GET /admin/pedidos`, `PATCH /pedidos/{id}/avanzar` | ADMIN, PEDIDOS |
| `GET /admin/usuarios`, `PUT/PATCH /admin/usuarios/{id}` | ADMIN |
| `GET/PUT /admin/metricas/*` | ADMIN |
| `GET/PUT /admin/configuracion` | ADMIN |

#### Scenario: ADMIN accesses admin endpoint
- **WHEN** a user with role ADMIN calls `GET /api/v1/admin/usuarios`
- **THEN** the system returns HTTP 200

#### Scenario: CLIENT cannot access admin endpoint
- **WHEN** a user with role CLIENT calls `GET /api/v1/admin/usuarios`
- **THEN** the system returns HTTP 403

#### Scenario: STOCK can manage products
- **WHEN** a user with role STOCK calls `POST /api/v1/productos`
- **THEN** the request proceeds past the auth guard (may return 422 if body invalid, but NOT 401/403)

#### Scenario: PEDIDOS cannot manage products
- **WHEN** a user with role PEDIDOS calls `POST /api/v1/productos`
- **THEN** the system returns HTTP 403
