## Why

The Food Store backend currently has no request schemas — all feature folders (`auth/`, `usuarios/`, `productos/`, etc.) are empty stubs. Before implementing any API endpoints, we need Pydantic v2 request/response schemas with field-level validation and XSS sanitization, so that invalid or malicious inputs are rejected at the boundary before reaching business logic.

## What Changes

- **New shared sanitization utility** at `backend/core/sanitize.py` — strips HTML/script tags from free-text inputs using `bleach` or regex
- **Request schemas for all 8 feature domains**: auth, usuarios, productos, categorias, ingredientes, pedidos, pagos, direcciones — each in their feature folder as `schemas.py`
- **Pydantic v2 validators** on every schema: email format (`EmailStr`), string min/max lengths, numeric ranges (precio > 0, stock >= 0, cantidad >= 1), phone format, URL format
- **XSS protection** applied via `field_validator` on all free-text fields: `nombre`, `descripcion`, `alias`, `observacion`, `referencia`
- **Documentation** that SQLModel parametrized queries already prevent SQL injection — no extra work needed

## Capabilities

### New Capabilities
- `input-validation-schemas`: Pydantic v2 request/response schemas with field-level validation (email, length, range, format) for all 8 feature domains
- `xss-sanitization`: Shared sanitization utility that strips HTML tags from text inputs, applied via Pydantic field validators

### Modified Capabilities
<!-- No existing specs change at the requirements level — this adds a new validation layer -->

## Impact

- **New files**: `backend/core/sanitize.py`, `backend/auth/schemas.py`, `backend/usuarios/schemas.py`, `backend/productos/schemas.py`, `backend/categorias/schemas.py`, `backend/ingredientes/schemas.py`, `backend/pedidos/schemas.py`, `backend/pagos/schemas.py`, `backend/direcciones/schemas.py`
- **Dependencies**: `pydantic[email]` (already included via FastAPI), optionally `bleach` for HTML stripping
- **No breaking changes** — these schemas are new files; no existing code references them yet
- **Unblocks**: all feature endpoint implementations (auth-login-register, products-crud, orders-fsm, etc.)
