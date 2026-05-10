## Context

The application already has login (`POST /api/v1/auth/login`) and token-refresh (`POST /api/v1/auth/refresh`) implemented and archived. The `RefreshToken` table in PostgreSQL has a `revoked_at TIMESTAMP WITH TIME ZONE` nullable column and the `auth-token-refresh` change already implemented revocation logic in `uow.refresh_tokens.update()`. The frontend `authStore` has a synchronous `logout()` action that clears local state but does not call any backend endpoint.

**Current gap**: A user who clicks "logout" only clears their browser state. The refresh token remains active in the database until its 7-day TTL expires, meaning it could still be exchanged for new access tokens if the token value is known.

## Goals / Non-Goals

**Goals:**
- Expose `POST /api/v1/auth/logout` that revokes a specific refresh token by setting `revoked_at = now()`.
- Return HTTP 204 No Content on success (no body).
- Return HTTP 401 if the token is unknown or already revoked (token not found in DB).
- Wire the frontend `logout()` action to call the backend endpoint before clearing local state.
- No new Alembic migrations — existing schema supports this.

**Non-Goals:**
- Revoking ALL sessions (that is replay-attack logic, already implemented in `auth-token-refresh`).
- Invalidating access tokens — they are stateless JWTs; they expire naturally (30 min). A future blocklist capability can address this if needed.
- Requiring authentication (Bearer header) to call logout — the refresh token itself serves as proof of session ownership.

## Decisions

### Decision 1: Logout endpoint is unauthenticated (uses refresh token as credential)

The endpoint accepts a `LogoutRequest { refresh_token: str }` body. No `Authorization: Bearer` header is required. The refresh token proves the caller owns the session.

**Rationale**: Requiring a valid access token to logout creates a catch-22 — if the access token has already expired (common scenario), the user cannot logout even though they hold a valid refresh token. Using the refresh token directly mirrors how `/auth/refresh` works and is simpler.

**Alternative considered**: Require `Authorization: Bearer <access_token>` and derive `usuario_id` from it to revoke all tokens. Rejected because it forces users with expired access tokens to refresh first just to logout, which is a bad UX and incorrect security posture.

### Decision 2: Return 204 even if the token is already revoked (idempotent logout)

If the client calls logout twice (e.g., tab duplication, retry on network error), the second call should not fail with 401. The endpoint treats an already-revoked token as "mission accomplished".

**Rationale**: Logout is a intent-based action. The user's goal is to end the session. If it's already ended, returning 401 confuses clients and requires special-case handling in the frontend. Idempotency is the correct HTTP semantic here (`DELETE`-like behavior: deleting something already deleted = 204).

**Alternative considered**: Return 401 for already-revoked tokens. Rejected — forces frontend to handle a non-error case as an error.

**Exception**: Token not found in DB (counterfeit token) → 401. Only genuinely unknown tokens are rejected; revoked tokens return 204.

### Decision 3: No new schema file in `auth/schemas.py` — reuse `RefreshRequest`

`LogoutRequest` would have exactly one field: `refresh_token: str`. This is identical to `RefreshRequest`. We reuse `RefreshRequest` as the input schema rather than creating a new type with the same shape.

**Rationale**: DRY. The schema already exists, is validated, and is tested. Adding a type alias creates cognitive overhead with no new behavior.

### Decision 4: Frontend logout becomes async; calls backend before clearing state

The current `logout()` in `authStore.ts` is a synchronous Zustand action. It needs to become an async call (or a wrapper function in the API layer) that:
1. POSTs to `/api/v1/auth/logout` with the current `refreshToken`.
2. Clears authStore state regardless of the HTTP response (best-effort revocation).

**Rationale**: Clearing local state is always correct regardless of network errors. If the backend is unreachable, the session expires naturally (7-day TTL). The user's local session is always terminated.

**Pattern used**: A `logoutUser()` function in `frontend/src/features/auth/api/authApi.ts` (or equivalent API layer) wraps the HTTP call. The UI component calls this function, which calls `authStore.logout()` after the request settles (success or failure).

## Risks / Trade-offs

- **Access token not revoked** → The access token (30-min JWT) remains valid after logout. An attacker who stole the access token can still use it until expiry. Mitigation: short 30-min TTL limits the window. Full token invalidation requires a server-side blocklist (out of scope).
- **Network failure on logout** → If the backend call fails, the frontend still clears local state, but the refresh token stays active in the DB. Mitigation: 7-day TTL acts as a safety net; the token cannot be obtained again from the cleared frontend. Risk is low in practice.
- **Idempotent 204 for revoked tokens** → A stolen refresh token could be "silently" accepted on logout by a malicious actor, preventing detection. Mitigation: the replay-attack detection on `/auth/refresh` still catches reuse attempts. The logout endpoint is not the place to detect theft.

## Migration Plan

1. Add `logout_user()` service function in `backend/auth/service.py`.
2. Add `POST /auth/logout` route in `backend/auth/router.py` (no rate limiting needed — token acts as credential).
3. Add `logoutUser()` API function in frontend auth API layer.
4. Update `authStore.ts` `logout()` or create a wrapper hook to call the API before clearing state.
5. No migrations. No seed changes.
6. Rollback: remove the route and revert the frontend to the synchronous logout — no data is affected.

## Open Questions

- None. The design is fully determined by existing patterns in the codebase.
