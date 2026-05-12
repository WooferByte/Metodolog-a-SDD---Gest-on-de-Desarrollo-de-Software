## Context

The frontend routing is built with react-router-dom v6 using `<Routes>` / `<Route>` in `frontend/src/app/Router.tsx`. A `withAuth` HOC exists at `frontend/src/shared/routing/withAuth.tsx` but is a non-functional stub (hardcoded `isAuthenticated = true`, inline style-based 403 UI).

The `useAuthStore` (Zustand v5, persist middleware) already tracks `isAuthenticated`, `user.roles`, `hasRole()`, and `_hasHydrated`. The hydration guard is critical: on page reload, Zustand loads from localStorage asynchronously — without `_hasHydrated`, the component renders with `isAuthenticated = false` for one frame and immediately redirects.

The project uses FSD architecture: auth guard belongs in `shared/routing/` (shared across layers). Pages live in `pages/`. The 403 page is a pure presentational page component.

## Goals / Non-Goals

**Goals:**
- Replace the `withAuth` stub with a real `ProtectedRoute` component that reads from `useAuthStore`
- Guard routes against unauthenticated access (redirect to `/login`) and insufficient roles (redirect to `/403`)
- Avoid redirect flash on page reload using the `_hasHydrated` guard
- Preserve `state={{ from: location }}` on login redirect so the app can redirect back post-login
- Add a styled `ForbiddenPage` component (Tailwind v4, accessible)
- Add `/403` route and wire `requiredRoles` per route group in `Router.tsx`
- Full vitest coverage of all guard scenarios

**Non-Goals:**
- Server-side rendering / SSR (app uses Vite + client-side only)
- Redirect-back post-login logic (belongs in the Login page change, not here)
- Persisting the last-visited URL across sessions
- Backend authorization changes

## Decisions

### Decision 1: `ProtectedRoute` as a layout route with `<Outlet />` vs. HOC wrapping

**Chosen**: Layout route pattern with `<Outlet />`, keeping `withAuth.tsx` as the file but replacing its implementation.

**Rationale**: React Router v6 layout routes are the idiomatic pattern for nested route protection. `<Outlet />` renders child routes, meaning a single `<ProtectedRoute>` instance protects an entire subtree. The HOC approach (`withAuth(Component)`) requires wrapping each component individually and doesn't compose well with nested routes. The file `withAuth.tsx` is already imported in `Router.tsx`; re-exporting `ProtectedRoute` from it avoids changing import paths.

**Alternative considered**: Keep HOC pattern, add real auth logic. Rejected because HOC wrapping doesn't support nested routes cleanly and creates per-component overhead.

### Decision 2: `_hasHydrated` → show loading skeleton, not blank screen

**Chosen**: While `!_hasHydrated`, render a minimal loading indicator (centered spinner div with Tailwind v4 classes) instead of null or a redirect.

**Rationale**: Rendering `null` on first frame can cause layout shift. A skeleton/spinner is better UX. The spinner must never persist if hydration is already complete — it only shows for the milliseconds before Zustand rehydrates from localStorage.

**Alternative considered**: Always redirect if `!isAuthenticated` without hydration check. Rejected: causes redirect flash on direct URL access and page reload.

### Decision 3: Role checking — `some()` (any of the required roles suffices)

**Chosen**: `requiredRoles.some(role => hasRole(role))` — access granted if user has at least one of the listed roles.

**Rationale**: ADMIN should be able to access CLIENT routes (cart, orders). Using `some()` allows listing `['CLIENT', 'ADMIN']` for CLIENT routes, so ADMIN users are not blocked. `hasRole()` already delegates to `user.roles.includes()` in the store.

**Alternative considered**: Require ALL roles (`every()`). Rejected: doesn't support ADMIN overrides without listing ADMIN everywhere explicitly.

### Decision 4: Redirect to `/403` (not inline 403 component)

**Chosen**: `<Navigate to="/403" replace />` redirects to the dedicated `ForbiddenPage` route.

**Rationale**: A proper route keeps the URL meaningful, allows the browser back button to work, and lets users bookmark or share the URL context. An inline 403 UI (as in the current stub) keeps the URL as `/admin/...` which is confusing.

**Alternative considered**: Render inline 403 content in `ProtectedRoute`. Rejected: misleading URL, harder to style independently.

## Risks / Trade-offs

- **Risk: `_hasHydrated` never becomes `true` if localStorage is corrupt** → Mitigation: `onRehydrateStorage` in authStore always calls `setHasHydrated(true)` even on error (already implemented in authStore.ts). Loading spinner will disappear.
- **Risk: Router.tsx has existing HOC-wrapped components** (`ProtectedProfile`, `ProtectedOrders`, `ProtectedAdmin`) → Mitigation: Replace all HOC usage with layout route pattern in the same file; no other files reference these wrapped components.
- **Trade-off: `withAuth.tsx` file name is kept but exports `ProtectedRoute`** — slightly misleading name. Acceptable to avoid a rename that would touch `Router.tsx` imports unnecessarily; JSDoc comment will clarify.
