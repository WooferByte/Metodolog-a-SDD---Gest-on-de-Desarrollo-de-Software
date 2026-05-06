# Authentication Dependencies Capability

## Overview

FastAPI dependencies for extracting, validating JWT tokens and providing current user context to route handlers.

## ADDED Requirements

#### Scenario: Protected route with current user
```python
@app.get("/api/v1/perfil")
async def get_profile(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "rol": current_user.rol,
    }
```

#### Scenario: Token extraction and validation
```python
# Header: "Authorization: Bearer eyJhbGc..."
# Extract token from header
# Validate JWT signature and expiration
# Query database for matching Usuario
# Return Usuario or raise 401
```

#### Scenario: Soft-deleted user cannot access
```python
# User has valid token but eliminado_en IS NOT NULL
# get_current_user() raises 403 Forbidden
```

## Requirements

### R1: Token Extraction
- Function: `def extract_token(auth_header: Optional[str] = Header(None, alias="authorization")) -> str`
- Expected format: "Bearer <token>"
- Raises 401 with message "Missing or invalid Authorization header" if:
  - Header is missing
  - Format is not "Bearer <token>"
  - Bearer is misspelled

### R2: JWT Verification
- Function: `async def verify_token(token: str) -> dict[str, Any]`
  - Uses `core.security.verify_token(token)` from CHANGE 0
  - Validates signature, expiration, standard claims (iss, aud)
  - Returns payload dict
  - Raises 401 if invalid/expired

### R3: User Lookup
- Function: `async def get_current_user(token: str = Depends(extract_token), session: AsyncSession = Depends(get_db)) -> Usuario`
- Extracts "sub" (user ID) from token payload
- Queries `SELECT * FROM usuarios WHERE id = ? AND eliminado_en IS NULL`
- Returns Usuario entity
- Raises 401 if user not found
- Raises 403 if user is soft-deleted (`eliminado_en IS NOT NULL`)

### R4: Role Information
- Usuario entity includes `rol_id` FK to Rol table
- JWT payload includes `roles` claim (optional, set during token creation)
- `get_current_user()` returns Usuario with all role info loaded

### R5: Caching (Optional)
- Optional: cache current user per request using `request.state.current_user`
- Prevents repeated database lookups if `get_current_user()` called multiple times in same request

### R6: Error Messages
- 401 Unauthorized: "Invalid or expired token"
- 401 Unauthorized: "Missing Authorization header"
- 403 Forbidden: "User account is disabled or deleted"

## Acceptance Criteria

- [ ] `extract_token()` dependency created
- [ ] `verify_token()` decodes and validates JWT
- [ ] `get_current_user()` returns Usuario entity
- [ ] 401 raised for missing/invalid tokens
- [ ] 403 raised for soft-deleted users
- [ ] Works with all future route handlers
- [ ] Request caching prevents N+1 queries (optional)
