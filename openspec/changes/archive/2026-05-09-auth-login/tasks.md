## 1. Verify Prerequisites

- [x] 1.1 Confirm `RefreshToken` SQLModel exists in `backend/auth/model.py` (fields: id, usuario_id, token, expires_at, revoked_at)
- [x] 1.2 Confirm `LoginRequest` and `TokenResponse` schemas exist in `backend/auth/schemas.py`
- [x] 1.3 Confirm `verify_password()`, `create_access_token()`, `create_refresh_token()` exist in `backend/core/security.py`
- [x] 1.4 Confirm slowapi `Limiter` instance is accessible (in `main.py` or `backend/core/limiter.py`)
- [x] 1.5 Confirm `app.state.limiter` and `app.add_exception_handler(RateLimitExceeded, ...)` are set in `main.py`

## 2. Add Dummy Hash for Timing Attack Prevention

- [x] 2.1 In `backend/auth/service.py`, define a module-level `DUMMY_HASH` constant — a pre-computed bcrypt hash of a random string — to use when user is not found

## 3. Implement `login_user()` in Service

- [x] 3.1 Add `async def login_user(db_session, login_data: LoginRequest) -> TokenResponse` to `backend/auth/service.py`
- [x] 3.2 Look up user by email using the repository; if not found, call `verify_password(login_data.password, DUMMY_HASH)` then raise `HTTPException(401, "Invalid credentials")`
- [x] 3.3 If found, call `verify_password(login_data.password, user.hashed_password)`; if False, raise `HTTPException(401, "Invalid credentials")`
- [x] 3.4 Build access token payload: `{ "sub": str(user.id), "email": user.email, "roles": [r.nombre for r in user.roles] }`
- [x] 3.5 Call `create_access_token(data=payload)` to generate the JWT (30-min expiry)
- [x] 3.6 Call `create_refresh_token()` to generate a UUID string
- [x] 3.7 Persist `RefreshToken(usuario_id=user.id, token=refresh_token, expires_at=now()+timedelta(days=7))` via UoW
- [x] 3.8 Return `TokenResponse(access_token=..., refresh_token=..., token_type="Bearer", usuario=UsuarioResponse.from_orm(user))`

## 4. Add `POST /auth/login` Route

- [x] 4.1 Import `Limiter` and `Request` in `backend/auth/router.py`
- [x] 4.2 Decorate the login endpoint with `@limiter.limit("5/15minutes")`
- [x] 4.3 Add `request: Request` as the first parameter (required by slowapi)
- [x] 4.4 Define `@router.post("/login", response_model=TokenResponse)` that delegates to `login_user()`
- [x] 4.5 Inject DB session via `Depends(get_session)` or the project's UoW dependency

## 5. Wire Rate Limiting in main.py (if not already done)

- [x] 5.1 Verify `app.state.limiter = limiter` is set in `main.py`
- [x] 5.2 Verify `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)` is registered
- [x] 5.3 If either is missing, add them in `main.py`

## 6. Tests

- [x] 6.1 Write `tests/auth/test_login.py` with: successful login returns 200 + tokens
- [x] 6.2 Test: wrong password returns 401 with `"Invalid credentials"`
- [x] 6.3 Test: unknown email returns 401 with `"Invalid credentials"`
- [x] 6.4 Test: `RefreshToken` row is created in DB on successful login
- [x] 6.5 Test: access token payload contains `sub`, `email`, `roles`
- [x] 6.6 Run all tests: `cd backend && python -m pytest tests/ -x -q`
