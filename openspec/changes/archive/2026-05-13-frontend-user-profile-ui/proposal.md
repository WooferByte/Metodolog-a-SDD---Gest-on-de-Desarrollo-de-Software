# Proposal: frontend-user-profile-ui

## Summary

Implement the authenticated user profile page (`/profile`) for Food Store, replacing the current stub. The page allows users to view their profile data, edit name and phone number, and change their password.

## Problem Statement

`/profile` currently renders a static stub (`"Esta página será implementada en CHANGE 6+"`). Authenticated users (CLIENT or ADMIN role) cannot view or manage their own profile data, making the app incomplete for end-to-end user self-service.

## Goals

- Replace `Profile.tsx` stub with a fully functional profile page.
- Consume the three existing backend endpoints:
  - `GET /api/v1/perfil` — fetch authenticated user's profile
  - `PUT /api/v1/perfil` — update `nombre` and/or `telefono`
  - `POST /api/v1/perfil/cambiar-password` — change password (revokes all refresh tokens, returns `204`)
- Show last session info derived from the authenticated state (token data available in `authStore`).
- No backend changes required — the API is already implemented and stable.

## Non-Goals

- Changing email address (backend does not expose this via perfil endpoints)
- Avatar/photo upload
- Address management (separate future change)
- Admin-level user management

## Scope

**Frontend only — no backend changes.**

| Layer | What changes |
|-------|-------------|
| `frontend/src/pages/Profile.tsx` | Replace stub with full page (lazy import already configured in Router.tsx) |
| `frontend/src/features/profile/` | New feature directory: hooks, components, types |
| `frontend/e2e/profile/` | E2E specs for guard, form submit, password change |

## User Stories Covered

- **HU-PE01**: Como usuario autenticado, quiero ver mis datos de perfil para verificar mi información.
- **HU-PE02**: Como usuario autenticado, quiero editar mi nombre y teléfono para mantener mi información actualizada.
- **HU-PE03**: Como usuario autenticado, quiero cambiar mi contraseña de forma segura.

## Technical Context

### Backend contracts (confirmed — read from source)

**GET `/api/v1/perfil`** → `UsuarioResponse`
- Returns: `{ id, email, nombre, telefono, roles, creado_en }` (no hashed_password, no eliminado_en)
- Auth: JWT required (`get_current_user`)
- Errors: 401

**PUT `/api/v1/perfil`** → `UsuarioResponse`
- Body: `PerfilUpdate { nombre?: str (1-100, HTML stripped), telefono?: str (max 20) }`
- Constraint: at least one field must be non-null (422 otherwise)
- Errors: 401, 422

**POST `/api/v1/perfil/cambiar-password`** → `204 No Content`
- Body: `CambiarPasswordRequest { password_actual: str (8-128), nueva_password: str (8-128) }`
- Constraint: nueva_password must differ from password_actual (422 otherwise)
- Side effect: revokes ALL active refresh tokens (user will need to log in again on other sessions)
- Errors: 400 (wrong current password), 401, 422

### Frontend context (confirmed — read from source)

- `Profile` is already lazy-imported in `Router.tsx` with `React.lazy` — no Router changes needed.
- Route guard: `<ProtectedRoute requiredRoles={['CLIENT', 'ADMIN']} />` wraps `/profile` — no changes needed.
- `authStore` (`food-store-auth` localStorage key): provides `user.email`, `user.name`, `isAuthenticated`, `_hasHydrated`.
- `apiClient` (Axios singleton): JWT interceptor auto-attaches `Authorization` header; 401 triggers refresh flow; non-401 errors dispatch RFC 7807 toasts to `uiStore`.
- Existing UI components available: `Button`, `Input`, `Card`/`CardHeader`/`CardContent`/`CardFooter`, `Badge`, `Spinner`, `Modal`, `Skeleton`.
- Design tokens in `frontend/src/index.css` `@theme`: semantic colors (`primary`, `muted`, `destructive`, `card`, `border`, `success`, `warning`, `info`), OKLCH color space, radius tokens.
- Tailwind v4 CSS-first — only semantic token classes allowed, no raw color utilities.

## Acceptance Criteria

- [ ] Visiting `/profile` without a session redirects to `/login`.
- [ ] Authenticated CLIENT and ADMIN can reach `/profile`.
- [ ] Profile data (email, nombre, telefono, roles, creado_en) loads from `GET /api/v1/perfil` via TanStack Query — no Zustand duplication.
- [ ] Loading state shows `Skeleton` placeholders (no layout shift).
- [ ] Edit profile form (nombre + telefono) submits via `PUT /api/v1/perfil`, shows success toast, refetches data.
- [ ] Change password form validates: both fields required, min 8 chars, new ≠ current — before sending to backend.
- [ ] On password change success (204): shows success toast "Contraseña actualizada. Iniciá sesión nuevamente.", then logs user out after 2 s.
- [ ] All form errors (422, 400) display inline via toast (Axios interceptor handles non-204 errors automatically).
- [ ] "Última sesión" section shows `creado_en` (formatted) as membership date, and current session email from `authStore`.
- [ ] All interactive elements keyboard-navigable; all inputs have visible labels; WCAG AA contrast.
- [ ] Fully responsive: single-column mobile, two-column desktop (profile info + forms side by side).
- [ ] No raw color classes — only semantic tokens from `@theme`.
- [ ] `npx vitest run` passes with ≥ 40% coverage on new feature files.
- [ ] E2E Playwright spec passes: guard redirect, form submit, password change flow.
