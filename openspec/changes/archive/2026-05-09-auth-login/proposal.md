## Why

The Food Store app requires authenticated access for purchases, order management, and admin operations. Without a login endpoint, users cannot obtain JWT tokens, and the RBAC system (4 roles: ADMIN, STOCK, PEDIDOS, CLIENT) cannot be enforced. This change introduces the core login endpoint that enables all role-protected features.

## What Changes

- **New endpoint** `POST /api/v1/auth/login`: accepts email + password, returns JWT access token + UUID refresh token
- **Rate limiting** on login endpoint: max 5 failed attempts per IP per 15 minutes (via slowapi) to prevent brute-force attacks
- **Refresh token persistence**: UUID token stored in `RefreshToken` table with `expires_at = now() + 7 days`
- **Generic error responses**: "Invalid credentials" regardless of whether email exists (prevents user enumeration)
- **Timing attack prevention**: dummy hash verification when user not found, so response time is consistent

## Capabilities

### New Capabilities

- `auth-login`: Login endpoint with bcrypt credential verification, JWT access token generation (30 min, HS256), refresh token creation and storage, rate limiting, and generic error responses

### Modified Capabilities

- `auth`: Existing auth capability gains login behavior alongside existing register endpoint

## Impact

- **Backend files**: `backend/auth/router.py`, `backend/auth/service.py`, `backend/auth/schemas.py` (existing — add login logic)
- **New DB writes**: `RefreshToken` table inserts on every successful login
- **Dependencies**: `slowapi` (rate limiting), `python-jose` (JWT), `passlib[bcrypt]` (password verification)
- **Security surface**: Credentials flow through POST body; bcrypt timing parity is critical
