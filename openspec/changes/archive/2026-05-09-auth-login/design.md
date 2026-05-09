## Context

The app already has `POST /api/v1/auth/register` in `backend/auth/router.py`, a `service.py` with `register_user()`, and supporting utilities in `backend/core/security.py` (`verify_password`, `create_access_token`, `create_refresh_token`). The `RefreshToken` SQLModel exists. slowapi is installed. We need to add the login endpoint following the same DDD vertical slice pattern.

Current gap: No way for users to authenticate and receive tokens. All role-protected routes are inaccessible.

## Goals / Non-Goals

**Goals:**
- `POST /api/v1/auth/login` endpoint that verifies bcrypt credentials and returns access + refresh tokens
- Rate limiting: 5 requests per IP per 15 minutes (slowapi `@limiter.limit`)
- Refresh token persisted to `RefreshToken` table (UUID, expires_at = now + 7 days)
- Generic 401 "Invalid credentials" for all failures (email not found OR wrong password)
- Consistent response time regardless of whether user exists (dummy hash verification)
- Access token payload: `{ sub: str(user_id), email: email, roles: [list of role names] }`
- Response schema: `TokenResponse { access_token, refresh_token, token_type="Bearer", usuario: UsuarioResponse }`

**Non-Goals:**
- Refresh token rotation endpoint (separate change)
- Logout / token revocation endpoint (separate change)
- Social / OAuth login
- Frontend integration

## Decisions

### D1: Timing attack prevention via dummy hash
**Decision**: When user lookup by email returns no row, call `verify_password(plain, DUMMY_HASH)` before raising 401.
**Why**: `bcrypt.checkpw` takes ~100ms. Without this, an attacker can enumerate valid emails by comparing response times. Raising 401 immediately on "user not found" leaks information.
**Alternative considered**: Constant-time sleep — rejected because it's fragile and doesn't mask actual computation variance.

### D2: Rate limiting keyed by IP, applied at the router level
**Decision**: Use `@limiter.limit("5/15minutes")` decorator on the login route, with slowapi's default IP key function.
**Why**: Brute-force protection must be at the network layer, not the service layer, so it activates before any DB I/O. 5 attempts / 15 min is a standard threshold that doesn't frustrate legitimate users.
**Alternative considered**: Application-level counter in Redis — rejected as over-engineering for current scale; slowapi covers the requirement.

### D3: Refresh token as UUID string stored in DB
**Decision**: Generate `uuid.uuid4()` as the refresh token, store in `RefreshToken` with `usuario_id`, `token`, `expires_at = now() + timedelta(days=7)`, `revoked_at = None`.
**Why**: UUIDs are cryptographically random and opaque. Storing them in DB enables future revocation without key rotation.
**Alternative considered**: Signed JWT refresh token — rejected because it can't be revoked without a denylist, and we want fine-grained revocation capability.

### D4: Access token payload includes roles list
**Decision**: Roles are embedded in the JWT payload as a list of role name strings.
**Why**: Allows authorization middleware to validate roles without a DB lookup on every request, keeping latency low.
**Trade-off**: If a user's roles change, existing tokens reflect old roles until expiry (30 min). Acceptable for this use case.

## Risks / Trade-offs

- **Dummy hash timing variance** → The dummy hash is a pre-computed bcrypt hash. On cold starts, first call may be slower; subsequent calls are warm. Acceptable.
- **Rate limit bypass via IP rotation** → slowapi IP-based limiting can be bypassed with proxies. A more robust solution would require account-level lockout (future change). Mitigation: current implementation matches spec requirement.
- **RefreshToken table growth** → Every login creates a new row. Without a cleanup job, the table grows unboundedly. Mitigation: add `expires_at` index; a periodic purge job is a future task.
- **slowapi Limiter wiring** → If the Limiter is not attached to the FastAPI app via `app.state.limiter`, the decorator silently no-ops. Must verify in `main.py`.

## Migration Plan

1. Verify `RefreshToken` table exists in DB (migration already run or run now)
2. Verify slowapi `Limiter` is attached to `app.state` in `main.py`
3. Add `login_user()` to `backend/auth/service.py`
4. Add `POST /auth/login` route to `backend/auth/router.py` with rate limit decorator
5. Run existing tests to ensure register flow still works
6. Deploy — no data migration required (additive only)

**Rollback**: Remove the new route and service method. No schema changes needed.

## Open Questions

- Is `RefreshToken` model already in `backend/auth/model.py`, or does it need to be added? (Verify before implementing.)
- Is the slowapi `Limiter` instance already exported from `main.py` or a `core/limiter.py`? (Verify import path.)
