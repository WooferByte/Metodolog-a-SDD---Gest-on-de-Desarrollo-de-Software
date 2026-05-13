# Design: backend-user-profile-endpoints

## Architecture

Follows the established Router → Service → UoW → Repository → Model flow. No new models or migrations are needed.

```
usuarios/
├── perfil_router.py     ← NEW: 3 endpoints, Depends(get_uow), response_model explicit
├── perfil_service.py    ← NEW: business logic — get_perfil, update_perfil, cambiar_password
├── perfil_schemas.py    ← NEW: PerfilUpdate, CambiarPasswordRequest
└── schemas.py           ← EXISTING: UsuarioResponse (reused as response model)

backend/tests/
└── test_perfil.py       ← NEW: unit tests with AsyncMock/MagicMock

main.py (or app router registration)  ← MODIFY: include perfil_router
```

### Why not reuse `usuarios/schemas.py UsuarioUpdate`?

`UsuarioUpdate` contains `activo` — a field that must never be user-editable. A dedicated `PerfilUpdate` schema exposes only `nombre` and `telefono`, enforcing least-privilege at the schema layer.

## Endpoints

### GET /api/v1/perfil

```
Authorization: Bearer <access_token>

200 OK
{
  "id": 1,
  "email": "user@example.com",
  "nombre": "Juan",
  "apellido": "Pérez",
  "activo": true,
  "telefono": "1122334455",
  "creado_en": "2026-01-01T00:00:00"
}

401 — missing or invalid JWT
```

- Dependency: `current_user: Usuario = Depends(get_current_user)`
- No UoW needed (user already loaded by dependency, no writes).
- Returns `UsuarioResponse.model_validate(current_user)` directly from the router — no service call needed; the router delegates to the service only for consistency and testability.

### PUT /api/v1/perfil

```
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "nombre": "Juan Carlos",   // optional, min_length=1, max_length=100, sanitized
  "telefono": "1199887766"   // optional, max_length=20
}

200 OK  → UsuarioResponse (updated)
422     → at least one field must be provided (validated in schema)
401     → no/bad JWT
```

- Body: `PerfilUpdate` — at least one field must be non-null (model_validator).
- Service: `update_perfil(current_user, data, uow)` — patches only provided fields, calls `uow.usuarios.update(usuario)`.
- `actualizado_en` is updated by `BaseRepository.update()` automatically.

### POST /api/v1/perfil/cambiar-password

```
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "password_actual": "OldPassword1",
  "nueva_password": "NewPassword1"
}

204 No Content  → success
400             → password_actual incorrecto
422             → nueva_password == password_actual, or length < 8
401             → no/bad JWT
```

- Validates `password_actual != nueva_password` at schema level (model_validator → 422).
- Service:
  1. `verify_password(data.password_actual, current_user.hashed_password)` — if False → 400.
  2. `current_user.hashed_password = hash_password(data.nueva_password)` — bcrypt cost from passlib context (configured in core; cost=12 per RN-AU04).
  3. Update usuario via `uow.usuarios.update(current_user)`.
  4. Revoke all active refresh tokens: `find_all_by(usuario_id=current_user.id)` on `uow.refresh_tokens`, set `revoked_at=datetime.utcnow()` on each non-revoked token, update each.
  5. Returns `None` → router sends 204.

**RN-AU04 implementation detail**: "active" tokens = those where `revoked_at IS NULL`. We use `find_all_by(usuario_id=...) ` and filter `revoked_at is None` in the service loop (avoids a raw SQL query, keeps within BaseRepository API).

## Schemas

### PerfilUpdate (perfil_schemas.py)

```python
class PerfilUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=20)

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitize_nombre(cls, v):
        if isinstance(v, str):
            return sanitize_text(v)
        return v

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.nombre is None and self.telefono is None:
            raise ValueError("Provide at least nombre or telefono")
        return self
```

### CambiarPasswordRequest (perfil_schemas.py)

```python
class CambiarPasswordRequest(BaseModel):
    password_actual: str = Field(min_length=8, max_length=128)
    nueva_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_must_differ(self):
        if self.password_actual == self.nueva_password:
            raise ValueError("nueva_password must differ from password_actual")
        return self
```

## Service Functions (perfil_service.py)

```python
async def get_perfil(current_user: Usuario) -> UsuarioResponse:
    """Return UsuarioResponse for the authenticated user (no DB call)."""

async def update_perfil(
    current_user: Usuario,
    data: PerfilUpdate,
    uow: UnitOfWork,
) -> UsuarioResponse:
    """Apply partial update. Returns updated UsuarioResponse."""

async def cambiar_password(
    current_user: Usuario,
    data: CambiarPasswordRequest,
    uow: UnitOfWork,
) -> None:
    """
    Validate current password, hash new one, update DB, revoke all refresh tokens.
    Raises HTTPException 400 if password_actual is wrong.
    """
```

## Router (perfil_router.py)

```python
router = APIRouter(prefix="/perfil", tags=["Perfil"])

@router.get("", response_model=UsuarioResponse, status_code=200)
async def get_perfil_endpoint(
    current_user: Usuario = Depends(get_current_user),
) -> UsuarioResponse: ...

@router.put("", response_model=UsuarioResponse, status_code=200)
async def update_perfil_endpoint(
    data: PerfilUpdate,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UsuarioResponse: ...

@router.post("/cambiar-password", response_model=None, status_code=204)
async def cambiar_password_endpoint(
    data: CambiarPasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> None: ...
```

## Registration in main.py

The `perfil_router` must be registered under `/api/v1`. Pattern matching existing `auth.router` registration:

```python
from usuarios.perfil_router import router as perfil_router
app.include_router(perfil_router, prefix="/api/v1")
```

## Error Format (RFC 7807)

All 4xx responses use the project-standard RFC 7807 format:

```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "Contraseña actual incorrecta",
  "instance": "/api/v1/perfil/cambiar-password"
}
```

## Test Strategy

File: `backend/tests/test_perfil.py`

All tests use `AsyncMock`/`MagicMock` — no live DB. Pattern follows `test_auth_login.py`.

| Test class | Scenarios |
|------------|-----------|
| `TestGetPerfilService` | Returns UsuarioResponse from current_user |
| `TestUpdatePerfilService` | Updates nombre only; updates telefono only; updates both; raises on empty body (schema-level) |
| `TestCambiarPasswordService` | Wrong password → 400; correct password → hashes new pw; revokes all active tokens; skips already-revoked tokens |
| `TestPerfilRouter` | GET 200; PUT 200; PUT 422 empty body; POST 204; POST 400 wrong pw; POST 422 same password; 401 no token |

## Security Checklist

- [x] All 3 endpoints require valid JWT via `get_current_user()`.
- [x] `PerfilUpdate` never exposes `activo`, `email`, or `hashed_password`.
- [x] `cambiar_password` validates existing password before accepting the new one.
- [x] All active refresh tokens revoked on password change (RN-AU04).
- [x] bcrypt cost=12 via passlib (configured globally — not overridden per-call).
- [x] `nueva_password == password_actual` rejected at schema level (422, not 400).
- [x] No email enumeration — 400 detail is generic ("Contraseña actual incorrecta").
