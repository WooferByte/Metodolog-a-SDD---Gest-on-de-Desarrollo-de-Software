## 1. Core dependency — require_role factory

- [x] 1.1 Read `backend/core/dependencies.py` to understand existing `get_current_user` implementation
- [x] 1.2 Implement `require_role(roles: list[str])` factory in `backend/core/dependencies.py` — returns a `Depends`-compatible async callable that calls `get_current_user` and checks role membership
- [x] 1.3 Return HTTP 403 RFC 7807 body when user role not in allowed list
- [x] 1.4 Verify HTTP 401 from `get_current_user` propagates unchanged for missing/invalid tokens

## 2. Login activo check

- [x] 2.1 Read `backend/auth/service.py` login function
- [x] 2.2 Add `activo` check in `auth/service.py`: raise HTTP 403 with detail "Cuenta desactivada" if `usuario.activo == False`

## 3. Apply guards — auth and user self-service routers

- [x] 3.1 Read `backend/auth/router.py` — logout uses refresh_token as proof, no require_role needed (design decision: token itself proves ownership)
- [ ] 3.2 `backend/usuarios/router.py` — NOT YET IMPLEMENTED (router does not exist, only schemas/role_router); apply when created in a future change
- [ ] 3.3 `backend/direcciones/router.py` — NOT YET IMPLEMENTED (only schemas exist); apply when created in a future change

## 4. Apply guards — catalog routers

- [ ] 4.1 `backend/productos/router.py` — NOT YET IMPLEMENTED (only schemas exist); apply when created in BLOQUE 3
- [ ] 4.2 `backend/categorias/router.py` — NOT YET IMPLEMENTED (only schemas exist); apply when created in BLOQUE 3
- [ ] 4.3 `backend/ingredientes/router.py` — NOT YET IMPLEMENTED (only schemas exist); apply when created in BLOQUE 3

## 5. Apply guards — pedidos and admin routers

- [ ] 5.1 `backend/pedidos/router.py` — NOT YET IMPLEMENTED (only schemas exist); apply when created in BLOQUE 4
- [ ] 5.2 `backend/admin/` — NOT YET IMPLEMENTED (empty dir with .gitkeep); apply when created

NOTE: `require_role` guard mapping is documented in `tests/test_route_protection.py` (section 7 comment block) for future router authors.

## 6. Tests

- [x] 6.1 Create `backend/tests/test_route_protection.py`
- [x] 6.2 Write `test_public_endpoint_no_token_returns_200` — GET /health and GET / without token → 200
- [x] 6.3 Write `test_protected_endpoint_no_token_returns_401` — PUT /api/v1/admin/users/{id}/role without token → 401
- [x] 6.4 Write `test_wrong_role_returns_403` — CLIENT/STOCK/PEDIDOS token on ADMIN-only endpoint → 403
- [x] 6.5 Write `test_correct_role_allows_access` — ADMIN token passes auth gate (not 401/403)
- [x] 6.6 Write require_role unit tests — correct role passes, wrong role raises 403, empty roles raises 403, multi-role user passes
- [x] 6.7 Write login activo check tests — inactive user → 403 "Cuenta desactivada", active user → TokenResponse
- [ ] 6.6 (future) Write `test_admin_accesses_admin_endpoints` — GET /admin/usuarios with ADMIN token (blocked by router not existing)
- [ ] 6.7 (future) Write `test_client_cannot_access_admin` — when admin router exists
- [ ] 6.8 (future) Write `test_stock_cannot_access_pedidos_mgmt` — when pedidos router exists
- [ ] 6.9 (future) Write `test_pedidos_role_cannot_manage_productos` — when productos router exists

## 7. Validation

- [x] 7.1 Run `cd backend && python -m pytest tests/test_route_protection.py -v` — 13/13 tests pass
- [x] 7.2 Run `cd backend && python -m pytest` — no regressions (27 pre-existing failures, 0 new failures, +13 new passes)
- [ ] 7.3 Run `cd backend && python -m black --check .` — black not installed in environment (pre-existing tooling gap)
- [ ] 7.4 Run `cd backend && python -m flake8 .` — flake8 not installed in environment (pre-existing tooling gap)
