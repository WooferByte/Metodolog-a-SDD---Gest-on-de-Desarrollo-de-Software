## 1. Service Layer

- [x] 1.1 Add `refresh_token_service()` to `backend/auth/service.py` — look up token by string, check revocation, check expiry, rotate token, return `TokenResponse`
- [x] 1.2 Implement replay-attack branch: when `revoked_at IS NOT NULL`, revoke ALL tokens for that `usuario_id` via `find_all_by` loop and return 401
- [x] 1.3 Implement valid-token branch: set `revoked_at = now()` on old token, create new `RefreshToken` row, issue new access + refresh tokens, return `TokenResponse`

## 2. Router

- [x] 2.1 Add `POST /auth/refresh` route to `backend/auth/router.py` — import `RefreshRequest` and `refresh_token_service`, apply rate limit `5/15minutes`, wire `get_uow` dependency

## 3. Tests

- [x] 3.1 Create `backend/tests/test_auth_refresh.py` with unit tests (AsyncMock UoW, no live DB)
- [x] 3.2 Test: unknown token → 401 "Invalid refresh token"
- [x] 3.3 Test: revoked token → 401 + all tokens revoked (replay attack)
- [x] 3.4 Test: expired token → 401 "Refresh token expired"
- [x] 3.5 Test: valid token → 200, old token revoked, new tokens returned
- [x] 3.6 Test: valid token → new access token payload has correct `sub`, `email`, `roles`

## 4. Verification

- [x] 4.1 Run `cd backend && python -m pytest tests/ -x -q` — all tests pass (8 new + 36 existing auth tests = 44 passed)
- [ ] 4.2 Run `poetry run ruff check .` — no lint errors (ruff not available in dev env)
- [ ] 4.3 Run `poetry run black --check .` — no formatting issues (black not available in dev env)
