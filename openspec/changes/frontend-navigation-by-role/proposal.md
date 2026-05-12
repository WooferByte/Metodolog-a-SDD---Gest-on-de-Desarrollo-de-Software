## Why

The existing `Navbar.tsx` only distinguishes between authenticated and unauthenticated users — it shows the same links regardless of role. Now that RBAC roles exist in the backend and `authStore` exposes `hasRole()`, the navigation must reflect each role's actual access surface. A CLIENT should never see admin links; a STOCK user should not see order management.

## What Changes

- Replace the existing `Navbar.tsx` (inline-styles, role-unaware) with a Tailwind v4 component that renders role-specific nav items.
- Add a `useNavLinks` hook in `shared/hooks/` that computes the visible link list from the current auth state + roles.
- Write vitest unit tests for `useNavLinks` covering all 5 states: unauthenticated, CLIENT, STOCK, PEDIDOS, ADMIN.
- No new pages, no new routes — only the navigation layer changes.

## Capabilities

### New Capabilities

- `role-based-navigation`: Navbar renders a dynamic link set derived from the authenticated user's role. Unauthenticated users see public links only; each role sees only its own section.

### Modified Capabilities

- `feature-sliced-frontend`: `shared/hooks/` gains `useNavLinks` — a hook that belongs to the shared layer per FSD rules.

## Impact

- `frontend/src/shared/components/Navbar.tsx` — full rewrite with Tailwind v4, role-aware links
- `frontend/src/shared/hooks/useNavLinks.ts` — new hook computing nav items from auth state
- `frontend/src/shared/hooks/__tests__/useNavLinks.test.ts` — vitest unit tests
- No changes to `Router.tsx`, pages, stores, or backend
