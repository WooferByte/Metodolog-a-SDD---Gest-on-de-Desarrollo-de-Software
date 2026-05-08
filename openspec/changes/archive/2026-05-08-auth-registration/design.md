# Design: auth-registration

## Architecture

Follows the DDD feature-first pattern: Router → Service → UoW → Repository → Model.

```
POST /api/v1/auth/register
        │
        ▼
auth/router.py          ← parse RegisterRequest, call service, return TokenResponse
        │
        ▼
auth/service.py         ← business logic: hash pw, create user, assign role, create tokens
        │
        ▼
infrastructure/uow.py   ← UnitOfWork (atomic transaction)
        │
        ├── uow.usuarios         → create Usuario
        ├── uow.roles            → lookup Rol by nombre="CLIENT"
        ├── uow.usuario_roles    → create UsuarioRol (pivot)
        └── uow.refresh_tokens   → store RefreshToken
```

## Flow Detail

1. Router receives `RegisterRequest` (validated by Pydantic v2)
2. Service calls `hash_password(data.password)` from `core.security`
3. Service creates `Usuario(email, hashed_password, nombre, apellido)` via `uow.usuarios.create()`
4. `await uow.session.flush()` gives the new user an ID (done inside `BaseRepository.create`)
5. Service looks up `Rol` where `nombre = "CLIENT"` via `uow.roles.find_by(nombre="CLIENT")`
6. Service creates `UsuarioRol(usuario_id=user.id, rol_id=rol.id)` via `uow.usuario_roles.create()`
7. Service calls `create_refresh_token(user.id)` to get a refresh token string
8. Service stores `RefreshToken(usuario_id, token, expires_at=now+7days)` via `uow.refresh_tokens.create()`
9. UoW `__aexit__` commits the entire transaction atomically
10. Service calls `create_access_token({sub: str(user.id), email, roles: ["CLIENT"]})` — NOT inside UoW (stateless JWT, no DB write)
11. Router returns `TokenResponse`

## Error Handling

| Situation | Error |
|-----------|-------|
| Duplicate email | IntegrityError → auto-caught → 409 Conflict (RFC 7807) |
| CLIENT role missing in DB | 500 Internal Error — seed data must be present |
| Pydantic validation fails | 422 Unprocessable Entity (automatic) |

## Security

- bcrypt cost: taken from `settings.bcrypt_cost` (>= 10)
- Refresh token stored as raw JWT in DB (for revocation support)
- Access token NOT stored in DB (stateless)
- Endpoint has no `require_role()` — it's public

## Files Changed

| File | Action |
|------|--------|
| `backend/auth/service.py` | CREATE — registration business logic |
| `backend/auth/router.py` | CREATE — FastAPI router with POST /register |
| `backend/auth/__init__.py` | CREATE — module init |
| `backend/main.py` | UPDATE — include auth router |
| `backend/tests/test_auth_register.py` | CREATE — unit tests |
