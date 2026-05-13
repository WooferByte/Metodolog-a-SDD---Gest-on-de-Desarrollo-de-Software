# Proposal: backend-user-profile-endpoints

## What

Implement three authenticated endpoints under `/api/v1/perfil` that let any logged-in user read and update their own profile data, and change their password with full session revocation:

| Method | Path | Summary |
|--------|------|---------|
| GET | `/api/v1/perfil` | Return the authenticated user's profile |
| PUT | `/api/v1/perfil` | Update `nombre` and/or `telefono` |
| POST | `/api/v1/perfil/cambiar-password` | Validate current password, hash new one (bcrypt cost=12), revoke all active refresh tokens |

## Why

- **US-063**: A logged-in user must be able to view and edit their own profile.
- **RN-AU04**: When a user changes their password, ALL active refresh tokens belonging to that user must be immediately revoked, forcing re-authentication on all devices.
- The `route-protection-rbac`, `auth-login`, and `auth-registration` changes are already archived — the `get_current_user()` dependency, `require_role()`, the UoW with `uow.usuarios` and `uow.refresh_tokens`, and `core/security.py` (`verify_password`, `hash_password`) are all available and tested.

## Out of Scope

- Email change (requires verification flow — future change).
- Admin editing another user's profile (covered by admin CRUD change).
- Adding or modifying fields beyond `nombre` and `telefono` in PUT.
- Any frontend UI (future frontend change).
- Alembic migration: `telefono` already exists in `usuarios` table (column added in `003_add_missing_fields.py`).

## Acceptance Criteria

1. `GET /api/v1/perfil` returns HTTP 200 with `UsuarioResponse` for valid JWT.
2. `GET /api/v1/perfil` returns HTTP 401 for missing/invalid JWT.
3. `PUT /api/v1/perfil` with valid body updates `nombre` and/or `telefono`, returns 200 with updated `UsuarioResponse`.
4. `PUT /api/v1/perfil` with an empty body (all fields `null`) returns 422.
5. `POST /api/v1/perfil/cambiar-password` with correct `password_actual` hashes `nueva_password` with bcrypt cost=12, saves to DB, revokes all active refresh tokens, returns 204.
6. `POST /api/v1/perfil/cambiar-password` with wrong `password_actual` returns 400 (not 401 — user IS authenticated).
7. `POST /api/v1/perfil/cambiar-password` where `nueva_password == password_actual` returns 422.
8. All endpoints require a valid JWT; unauthenticated requests receive 401.
9. All endpoints follow RFC 7807 error format for 4xx errors.
10. Test coverage for `perfil/service.py` >= 80% (unit tests with mocks, no live DB).

## Dependencies

- `route-protection-rbac` — ✅ archived (provides `require_role`, `get_current_user`)
- `auth-login` — ✅ archived (provides UoW, `uow.refresh_tokens`, `verify_password`)
- `auth-registration` — ✅ archived (provides `hash_password`, `UsuarioResponse`)
