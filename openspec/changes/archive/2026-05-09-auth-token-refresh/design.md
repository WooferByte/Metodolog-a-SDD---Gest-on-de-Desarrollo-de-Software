## Context

The `refresh_tokens` table already exists with `id`, `usuario_id`, `token` (JWT string), `expires_at`, and `revoked_at` columns. The `BaseRepository.find_by()` and `find_all_by()` helpers cover lookup by token string and by `usuario_id`. `create_refresh_token()` and `verify_token()` already exist in `core/security.py`. The UoW exposes `uow.refresh_tokens` as a `BaseRepository[RefreshToken]`.

## Goals / Non-Goals

**Goals**
- One-time-use refresh tokens via rotation (old revoked, new issued every call).
- Replay-attack detection: using a revoked token triggers full family revocation.
- Atomic DB operations inside a single UoW transaction.

**Non-Goals**
- No logout endpoint (out of scope for this change).
- No HTTP-Only cookie transport (Bearer header only, per existing convention).
- No family-tree graph — family is simply all rows with the same `usuario_id`.

## Decisions

### D1: DB lookup by token string, not JWT sub claim

Look up the token row by the raw JWT string (`uow.refresh_tokens.find_by(token=data.refresh_token)`) rather than decoding the JWT first. This lets us distinguish "token not in DB" (counterfeit/never issued) from "token is revoked" (replay) before doing any cryptographic work.

**Alternatives considered**: decode JWT first → `verify_token()` rejects expired tokens before replay check, so we'd never detect replay on expired tokens. Rejected: checking DB first is safer.

### D2: `find_all_by(usuario_id=...)` for family revocation

The replay attack revocation path calls `uow.refresh_tokens.find_all_by(usuario_id=usuario_id)` and sets `revoked_at = now()` on every row. This is simple and correct; the `find_all_by` method does NOT filter by `eliminado_en` (RefreshToken has no such field), so it returns all rows including already-revoked ones — safe to re-revoke them.

### D3: Access token roles fetched via `usuario.roles` relationship

After validating the refresh token, load the user via `uow.usuarios.get_by_id(usuario_id)` and read `usuario.roles` to build the token payload — consistent with the login flow.

### D4: Rate limit inherited from login (5/15min per IP)

The `/auth/refresh` endpoint is rate-limited identically to `/auth/login` using the existing `slowapi` limiter. Refresh abuse (e.g. token stuffing) is mitigated by the one-time-use rotation, so the same rate limit is sufficient.

## Risks / Trade-offs

- [Clock skew on `expires_at`] → Tolerate: `expires_at` is set server-side at creation; only checked server-side on refresh. No cross-server skew concern.
- [Family revocation revokes ALL sessions] → By design: replay attack means a token was leaked; nuking all sessions is the correct security response.
- [N+1 on family revocation] → Acceptable: revocation is a rare security event; a simple loop with per-row `session.add` and a single `flush` at commit is fine at current scale.

## Migration Plan

1. No DB migrations needed — `revoked_at` column already exists.
2. Deploy: new endpoint is additive; zero downtime.
3. Rollback: remove the route registration from `router.py` — no data changes to undo.

## Open Questions

None — all design decisions are resolved.
