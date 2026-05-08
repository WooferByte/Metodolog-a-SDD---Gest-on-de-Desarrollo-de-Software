# Proposal: auth-registration

## What
Implement the `POST /api/v1/auth/register` endpoint that allows new users to self-register on the Food Store platform.

## Why
The platform needs a public registration endpoint so customers can create accounts without admin intervention. This is the entry point for the CLIENT user journey.

## Scope
- Backend only
- Feature folder: `backend/auth/`
- New files: `model.py` (no — already in core), `service.py`, `router.py`, `__init__.py`
- Update: `backend/main.py` to include the auth router

## Acceptance Criteria
1. `POST /api/v1/auth/register` accepts `{ email, password, nombre, apellido? }`
2. Email uniqueness enforced — duplicate → 409 Conflict (auto via IntegrityError middleware)
3. Password hashed with bcrypt cost >= 10
4. CLIENT role assigned automatically from DB (not hardcoded)
5. RefreshToken stored in DB with expires_at = now + 7 days
6. Response: `{ access_token, refresh_token, token_type, usuario: {...} }`
7. Access token payload: `{ sub: str(user_id), email, roles: ["CLIENT"] }`
8. Endpoint is public — no authentication required
9. Validation enforced by Pydantic v2 (min_length=8 password, min_length=1 nombre)

## Out of Scope
- Login endpoint (separate change)
- Token refresh endpoint (separate change)
- Email verification flow
