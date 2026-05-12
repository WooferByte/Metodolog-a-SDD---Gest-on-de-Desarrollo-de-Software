## Why

With RBAC roles defined and JWT authentication in place, endpoints remain unprotected — any authenticated user (or even unauthenticated requests) can reach admin and stock operations. This change wires role enforcement into the FastAPI dependency layer so every endpoint declares its required roles explicitly and violations return consistent RFC 7807 responses.

## What Changes

- Implement `require_role(roles: list[str])` factory in `backend/core/dependencies.py` — returns a FastAPI `Depends`-compatible callable that reads the JWT payload and enforces role membership.
- Apply `require_role` to all protected endpoints across `auth`, `direcciones`, `pedidos`, `productos`, `categorias`, `ingredientes`, and `admin` routers.
- Public endpoints (`POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /productos`, `GET /productos/{id}`, `GET /categorias`) remain unauthenticated.
- 401 on missing/invalid token; 403 on insufficient role — both as RFC 7807 bodies.
- 8 unit tests covering role matrix: public pass-through, missing token, wrong role, correct role for each role group.

## Capabilities

### New Capabilities

- `route-protection`: FastAPI dependency `require_role` that enforces RBAC on endpoints. Covers the factory function, role-check logic, 401/403 error shapes, and the mapping of roles to endpoint groups.

### Modified Capabilities

- `auth-login`: Login now validates `usuario.activo == True` before issuing tokens (403 if inactive). Requirement extension on top of the existing login spec.
- `rbac-role-assignment`: All routers now apply the role guards defined in this spec. The assignment spec gains a section on how roles map to HTTP verbs.

## Impact

- `backend/core/dependencies.py` — new `require_role` factory (alongside existing `get_current_user`)
- All routers in `backend/auth/`, `backend/direcciones/`, `backend/pedidos/`, `backend/productos/`, `backend/categorias/`, `backend/ingredientes/` — add `dependencies=[Depends(require_role([...]))]` per endpoint
- `backend/tests/test_route_protection.py` — new test file (8 tests)
- No schema or DB changes — purely dependency/router layer
