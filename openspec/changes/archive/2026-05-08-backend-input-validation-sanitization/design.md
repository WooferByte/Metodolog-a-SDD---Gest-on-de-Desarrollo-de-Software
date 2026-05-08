## Context

The Food Store FastAPI backend has all domain models in `core/models.py` (16 SQLModel tables) but **no request/response schemas** anywhere. Feature folders (`auth/`, `usuarios/`, `productos/`, etc.) are empty. This change creates the validation layer before any endpoints are implemented.

Current state:
- SQLModel models exist in `core/models.py` — these are DB-layer models, NOT for request validation
- RFC 7807 error middleware is wired — 422 Unprocessable Entity is already formatted correctly
- No Pydantic schemas exist for incoming API requests
- Feature folders are empty stubs

Constraints:
- Pydantic v2 (shipped with FastAPI 0.100+) — use `model_validator`, `field_validator`, `@model_validator(mode='before')`
- SQLModel already uses parametrized queries — SQL injection is NOT a concern
- `pydantic[email]` is available via FastAPI dependency
- No `bleach` installed yet — use `re` (stdlib) for HTML tag stripping to avoid new dependency

## Goals / Non-Goals

**Goals:**
- Create `backend/core/sanitize.py` — a shared utility to strip HTML/script tags from strings
- Create `schemas.py` in each of the 8 feature folders with Pydantic v2 request schemas
- Apply `EmailStr` on email fields, min/max on strings, `gt=0` / `ge=0` on numerics
- Apply the sanitization utility on all free-text fields via `@field_validator`
- Keep schemas separate from DB models (single responsibility)

**Non-Goals:**
- Implementing routers, services, or repositories — this change is schemas only
- Validating business rules (e.g., user exists, product in stock) — that belongs in services
- Adding `bleach` as a new dependency — stdlib `re` is sufficient for tag stripping
- Changing existing `core/models.py` — DB models are untouched

## Decisions

### Decision 1: Separate schemas from DB models
**Choice**: Each feature gets its own `schemas.py` (e.g., `auth/schemas.py`, `productos/schemas.py`) separate from `core/models.py`.

**Rationale**: DB models (SQLModel table=True) expose fields like `hashed_password`, `eliminado_en`, `creado_en` that must never be in API contracts. Separation also allows request schemas to have stricter validators without affecting DB layer.

**Alternative considered**: Using SQLModel's built-in validation on table models — rejected because table models serve persistence, not API validation; mixing concerns makes both harder to evolve.

### Decision 2: Shared sanitizer in core/sanitize.py
**Choice**: One function `sanitize_text(value: str) -> str` using `re.sub` to strip HTML tags, living in `backend/core/sanitize.py`.

**Rationale**: Applied identically across all feature schemas. Centralizing avoids copy-paste and makes it easy to upgrade (e.g., swap `re` for `bleach`) in one place.

**Alternative considered**: Per-schema inline regex — rejected because it duplicates logic and makes upgrades error-prone.

### Decision 3: Pydantic v2 field_validator for sanitization
**Choice**: Decorate text fields with `@field_validator('nombre', 'descripcion', mode='before')` that calls `sanitize_text`.

**Rationale**: Pydantic v2 `field_validator` with `mode='before'` runs before type coercion, ensuring sanitization happens on raw input. This is the idiomatic Pydantic v2 pattern.

**Alternative considered**: FastAPI middleware that rewrites request bodies — rejected because it's fragile, hard to test, and doesn't integrate with Pydantic's validation error reporting.

### Decision 4: No validation of SQL injection
**Choice**: Document that SQLModel ORM handles it; no extra sanitization needed.

**Rationale**: SQLModel uses SQLAlchemy's parametrized queries. User input never reaches raw SQL strings. Adding manual SQL escaping would be redundant and could introduce false security.

## Risks / Trade-offs

- **[Risk] Regex-based HTML stripping is not a full sanitizer** → Mitigation: Strip any `<...>` tag sequence which covers all HTML/script injection. If richer sanitization is needed later, swap to `bleach` in `core/sanitize.py` without touching schemas.
- **[Risk] Schemas become out of sync with DB models** → Mitigation: Keep field names consistent between schemas and models; use code review checklist item to verify.
- **[Risk] Over-validation breaks legitimate data** → Mitigation: Use generous but safe bounds (e.g., nombre max_length=255 matching DB constraint, not 50); numeric ranges match business rules only.

## Migration Plan

1. Create `backend/core/sanitize.py`
2. Create `schemas.py` in each of the 8 feature folders
3. Write unit tests for sanitize utility and spot-check validators
4. No migration needed — schemas are new files with no existing consumers

## Open Questions

- None. Schema design is unambiguous from the ERD v5 model fields.
