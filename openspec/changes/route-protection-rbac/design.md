## Context

JWT authentication and RBAC roles exist (`get_current_user` in `core/dependencies.py`, roles seeded with stable IDs: ADMIN=1, STOCK=2, PEDIDOS=3, CLIENT=4). All routers are registered in `main.py` but no endpoint currently checks roles — any token grants access to everything.

The FastAPI dependency injection system is already used for `get_current_user`. The `require_role` guard is a natural extension: a factory that returns a Depends-callable wrapping `get_current_user` and adding a role membership check.

## Goals / Non-Goals

**Goals:**
- Implement `require_role(roles: list[str])` factory in `core/dependencies.py`
- Apply guards to all protected endpoints across 7 router modules
- Return RFC 7807 bodies for 401 (no/invalid token) and 403 (wrong role)
- Keep public endpoints completely unauthenticated (no token required)
- 8 unit tests covering the full role matrix

**Non-Goals:**
- Ownership checks (e.g., client can only read own pedidos) — handled inside service layer, not in the guard
- Fine-grained action-level permissions beyond role membership
- Changes to the JWT format or token issuance

## Decisions

**Decision 1 — Factory pattern over decorator**
`require_role(["ADMIN"])` returns a callable accepted by `Depends()`. Alternative was a custom decorator. FastAPI's dependency system handles injection natively; a factory composes cleanly with `get_current_user` as a sub-dependency and is fully testable by overriding dependencies in tests.

**Decision 2 — 401 vs 403 boundary**
- 401: token missing, malformed, or expired — this is `get_current_user`'s existing responsibility.
- 403: valid token but role not in the allowed list — `require_role`'s responsibility.
Separating these means `require_role` only needs to handle the role check; auth failures bubble up from the existing guard unchanged.

**Decision 3 — Role names as strings, not Enum**
Roles are compared by `nombre` field (string) from the JWT payload or DB. Using strings avoids coupling `core/dependencies.py` to a roles module and matches the seed data pattern already in use.

**Decision 4 — `activo` check in login, not in `require_role`**
The `activo` field check (403 if user is inactive) belongs in `auth/service.py` at login time, not in every request guard. This is consistent with session invalidation: a deactivated user's existing tokens expire naturally (30 min access token); revoking refresh tokens handles the rest.

## Risks / Trade-offs

`require_role` depends on `get_current_user` injecting the user object — if the user's roles aren't eagerly loaded from DB, the check could fail silently → Mitigation: ensure the user query in `get_current_user` joins or lazy-loads `roles`.

Applying guards to every endpoint manually is error-prone (a missed endpoint leaves a hole) → Mitigation: test file covers each role group's boundary; the 8 tests serve as a regression net.

## Migration Plan

1. Implement `require_role` in `core/dependencies.py`
2. Apply guards endpoint by endpoint per router (no DB migration needed)
3. Run `pytest tests/test_route_protection.py` — all 8 tests must pass
4. Run full suite `pytest --cov` — no regressions
5. No rollback risk: removing a `Depends(require_role(...))` call is a one-line revert per endpoint
