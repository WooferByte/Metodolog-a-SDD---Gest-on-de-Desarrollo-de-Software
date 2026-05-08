# Tasks: auth-registration

## Implementation Checklist

- [x] Create `backend/auth/__init__.py`
- [x] Create `backend/auth/service.py` — `register_user(data, uow)` function
- [x] Create `backend/auth/router.py` — `POST /auth/register` route
- [x] Update `backend/main.py` — include auth router with prefix `/api/v1`
- [x] Create `backend/tests/test_auth_register.py` — unit tests for service + router

## Acceptance Verification

- [x] Duplicate email → 409 (IntegrityError auto-caught)
- [x] Password hashed with bcrypt (not stored plain)
- [x] CLIENT role looked up from DB, not hardcoded
- [x] RefreshToken stored with correct expires_at
- [x] TokenResponse returned with access_token + refresh_token
- [x] Endpoint accessible without auth header
