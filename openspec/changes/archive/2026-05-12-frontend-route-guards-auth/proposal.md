## Why

The frontend currently has a `withAuth` HOC stub that always renders components regardless of authentication state (hardcoded `isAuthenticated = true`). Users can navigate to protected routes without being authenticated or having the required roles, creating a security gap in the UI layer. This change wires the auth guards to the real Zustand `useAuthStore` and adds a proper 403 Forbidden page.

## What Changes

- Replace the `withAuth` stub implementation in `frontend/src/shared/routing/withAuth.tsx` with a real `ProtectedRoute` component backed by `useAuthStore`
- Add `_hasHydrated` guard to prevent premature redirects on page reload (store rehydration from localStorage)
- Redirect unauthenticated users to `/login` with `state={{ from: location }}` for redirect-back post-login
- Add `frontend/src/pages/ForbiddenPage.tsx` — a styled 403 page with "Volver al inicio" button
- Update `frontend/src/app/Router.tsx` to use `<ProtectedRoute>` as a layout route with `<Outlet />` and assign correct `requiredRoles` per route group
- Add `/403` route pointing to `ForbiddenPage`
- Write vitest unit tests for all guard scenarios in `frontend/src/shared/routing/__tests__/ProtectedRoute.test.tsx`

## Capabilities

### New Capabilities

- `route-guards`: Client-side route protection using `ProtectedRoute` component — authentication check, role-based access control, hydration-safe redirect logic, and `<Outlet />`-based nested route composition.
- `forbidden-page`: Dedicated 403 Forbidden page component with Tailwind v4 styling and navigation back to home.

### Modified Capabilities

- (none — `withAuth.tsx` is being replaced, not changing existing spec-level behavior of another capability)

## Impact

- **Files modified**: `frontend/src/shared/routing/withAuth.tsx`, `frontend/src/app/Router.tsx`
- **Files created**: `frontend/src/pages/ForbiddenPage.tsx`, `frontend/src/shared/routing/__tests__/ProtectedRoute.test.tsx`
- **Dependencies**: `useAuthStore` (already implemented), `react-router-dom` v6 (already installed), `vitest` + `@testing-library/react` (already installed)
- **No backend changes**: guards are purely frontend
- **No new npm packages required**
