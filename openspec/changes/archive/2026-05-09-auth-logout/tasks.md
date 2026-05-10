## 1. Backend — Schema

- [x] 1.1 Open `backend/auth/schemas.py` and confirm `RefreshRequest` exists with a `refresh_token: str` field — no new schema needed (reuse per design Decision 3)

## 2. Backend — Service

- [x] 2.1 Add `logout_user(data: RefreshRequest, uow: UnitOfWork) -> None` function in `backend/auth/service.py`
- [x] 2.2 Inside `logout_user`: look up `RefreshToken` by `token=data.refresh_token` via `uow.refresh_tokens.find_by(token=...)`
- [x] 2.3 If token not found: raise `HTTPException(401, "Invalid refresh token")`
- [x] 2.4 If token found and `revoked_at IS NULL`: set `token_record.revoked_at = datetime.now(UTC)` and call `uow.refresh_tokens.update(token_record)`
- [x] 2.5 If token found and `revoked_at IS NOT NULL`: do nothing (already revoked — idempotent 204)
- [x] 2.6 Return `None` (caller returns 204)

## 3. Backend — Router

- [x] 3.1 Import `logout_user` from `auth.service` in `backend/auth/router.py`
- [x] 3.2 Add `POST /auth/logout` route with `status_code=204`, `response_model=None`, summary "Logout and revoke refresh token"
- [x] 3.3 Route body: `data: RefreshRequest`, dependency: `uow: UnitOfWork = Depends(get_uow)`
- [x] 3.4 Route body calls `async with uow: await logout_user(data, uow)` and returns `None`
- [x] 3.5 Add responses doc: `204: {"description": "Token revoked or already revoked"}`, `401: {"description": "Token not found"}`
- [x] 3.6 Do NOT add `@limiter.limit()` — refresh token acts as credential, no brute-force surface

## 4. Frontend — API Layer

- [x] 4.1 Locate the auth API file (likely `frontend/src/features/auth/api/` or `frontend/src/shared/api/`) — create `logoutUser(refreshToken: string): Promise<void>` function
- [x] 4.2 Implement `logoutUser` using the existing axios instance: `POST /api/v1/auth/logout` with body `{ refresh_token: refreshToken }`, expect 204
- [x] 4.3 The function should not throw on 204; if the backend returns an error, let it propagate (caller handles it with best-effort logic)

## 5. Frontend — AuthStore Wiring

- [x] 5.1 Create or update a `useLogout` hook (or equivalent helper) that:
  - Reads `refreshToken` from `useAuthStore`
  - Calls `logoutUser(refreshToken)` wrapped in try/catch
  - Always calls `useAuthStore.getState().logout()` in the finally block (clears local state regardless of backend response)
- [x] 5.2 Update any UI component(s) with a "Logout" button to use the new async logout flow instead of directly calling `authStore.logout()`
- [x] 5.3 Ensure the component shows a loading/disabled state during the async call to prevent double-submission

## 6. Tests — Backend

- [x] 6.1 Add test: `POST /auth/logout` with a valid active refresh token → 204 and `revoked_at` is set in DB
- [x] 6.2 Add test: `POST /auth/logout` with a previously revoked token → 204 (idempotent)
- [x] 6.3 Add test: `POST /auth/logout` with a token string not in DB → 401

## 7. Tests — Frontend

- [x] 7.1 Add test for `logoutUser()` API function: mocks axios, asserts POST to correct URL with correct body
- [x] 7.2 Add test for `useLogout` hook (or wrapper): asserts `authStore.logout()` is called even when `logoutUser` throws

## 8. Verification

- [x] 8.1 Run `cd backend && poetry run pytest --cov=auth -v` — all tests pass
- [x] 8.2 Run `cd backend && poetry run ruff check . && poetry run black --check .` — no lint errors
- [x] 8.3 Run `cd frontend && npm run test` — all tests pass
- [ ] 8.4 Manual: login → copy refresh token → call `POST /api/v1/auth/logout` → confirm 204 → call `POST /api/v1/auth/refresh` with same token → confirm 401 "Invalid refresh token"
- [ ] 8.5 Manual: call `POST /api/v1/auth/logout` twice with same token → both return 204
- [ ] 8.6 Manual: click Logout in UI → confirm browser state cleared + redirect to login page
