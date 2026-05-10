## Why

With login and token-refresh in place, users have no secure way to end their session. Without a logout endpoint, refresh tokens persist indefinitely in the database even after a user intends to stop using the application, leaving active tokens as a permanent attack surface.

## What Changes

- **New endpoint** `POST /api/v1/auth/logout`: accepts the current refresh token in the request body, marks it as revoked (`revoked_at = now()`), and returns HTTP 204 No Content.
- **Backend auth module** (`backend/auth/`): new `logout` method in `AuthService`, new `logout` method in `AuthRepository` (reuses the revocation logic already present for token-refresh), and a new route registered in `AuthRouter`.
- **Frontend authStore** (`logout()` action): calls `POST /api/v1/auth/logout` with the stored refresh token, then clears all auth state (tokens, user) from Zustand store and localStorage — existing `logout()` stub now wired to the real endpoint.
- No database schema changes — the `revoked_at` column on `RefreshToken` already exists.
- No new Alembic migrations needed.

## Capabilities

### New Capabilities

- `auth-logout`: Logout endpoint that accepts a refresh token and revokes it, terminating the user's session server-side.

### Modified Capabilities

- `zustand-auth-store`: The existing `logout()` action requirement is extended — it must now call the backend logout endpoint before clearing local state, so revocation is server-side not just client-side.

## Impact

- **Backend**: `backend/auth/repository.py`, `backend/auth/service.py`, `backend/auth/router.py` — additive changes only (new method + new route).
- **Frontend**: `frontend/src/features/auth/` (authStore or API layer) — `logout()` becomes async, calls `POST /api/v1/auth/logout`.
- **No breaking changes**: existing login and refresh flows are untouched.
- **Security posture improved**: refresh tokens are explicitly revoked on logout instead of expiring passively.
