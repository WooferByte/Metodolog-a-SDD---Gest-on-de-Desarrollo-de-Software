## Why

The current authentication system issues refresh tokens but has no endpoint to use them — once an access token expires, the user is forced to log in again. Implementing `POST /api/v1/auth/refresh` with rotation and replay-attack detection closes this gap and meets the security standard described in `Historias_de_usuario.txt`.

## What Changes

- **New endpoint**: `POST /api/v1/auth/refresh` accepts a `RefreshRequest` (has `refresh_token` field, already defined in `auth/schemas.py`) and returns a `TokenResponse` with new tokens.
- **Token rotation**: on each successful refresh the old `RefreshToken` row is revoked (`revoked_at = now()`) and a new one is inserted, so each token can only be used once.
- **Replay-attack detection**: if a refresh token is presented whose `revoked_at` is already set, ALL `RefreshToken` rows for that user are immediately revoked and a 401 is returned — this invalidates every active session, forcing re-login.
- **Expiry check**: tokens past `expires_at` are rejected with 401.
- **New service function**: `refresh_token_service()` added to `backend/auth/service.py`.
- **Router registration**: new route added to `backend/auth/router.py`.

## Capabilities

### New Capabilities

- `jwt-refresh`: JWT refresh-token rotation endpoint with replay-attack detection — covers the full lifecycle from validating a refresh token in the DB, revoking it, issuing a new pair, and handling replay attacks.

### Modified Capabilities

<!-- none — existing register/login auth flows are unchanged -->

## Impact

- `backend/auth/service.py` — adds `refresh_token_service()` function
- `backend/auth/router.py` — adds `POST /auth/refresh` route
- `backend/auth/schemas.py` — `RefreshRequest` already exists, no changes needed
- `backend/core/security.py` — `verify_token()`, `create_access_token()`, `create_refresh_token()` consumed as-is
- `backend/tests/test_auth_refresh.py` — new test file
- No DB schema changes required (`refresh_tokens` table already has `revoked_at` column)
