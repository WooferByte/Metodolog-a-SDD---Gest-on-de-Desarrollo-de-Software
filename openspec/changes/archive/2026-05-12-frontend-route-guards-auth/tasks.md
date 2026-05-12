## 1. Replace withAuth stub with ProtectedRoute

- [x] 1.1 Replace the contents of `frontend/src/shared/routing/withAuth.tsx` with a `ProtectedRoute` component that reads `isAuthenticated`, `_hasHydrated`, and `hasRole` from `useAuthStore`
- [x] 1.2 Add hydration guard: when `_hasHydrated = false`, render a loading spinner (Tailwind v4 classes only, no inline styles)
- [x] 1.3 Add authentication check: when `!isAuthenticated`, render `<Navigate to="/login" state={{ from: location }} replace />`
- [x] 1.4 Add role check: when `requiredRoles` is defined and `!requiredRoles.some(r => hasRole(r))`, render `<Navigate to="/403" replace />`
- [x] 1.5 When all checks pass, render `<Outlet />` for nested route composition
- [x] 1.6 Export both `ProtectedRoute` (named) and keep `withAuth` as a named re-export alias for backward compatibility

## 2. Create ForbiddenPage (403)

- [x] 2.1 Create `frontend/src/pages/ForbiddenPage.tsx` with a semantic `<h1>` heading ("Acceso denegado") and descriptive paragraph
- [x] 2.2 Add a "Volver al inicio" button using `useNavigate` that navigates to `/`
- [x] 2.3 Style entirely with Tailwind v4 utility classes (no `style={{}}` props); ensure WCAG AA contrast and visible focus ring on button

## 3. Update Router.tsx with layout route pattern

- [x] 3.1 Remove the HOC-wrapped component declarations (`ProtectedProfile`, `ProtectedOrders`, `ProtectedAdmin`) from `Router.tsx`
- [x] 3.2 Add `/403` route pointing to `<ForbiddenPage />`
- [x] 3.3 Wrap CLIENT routes (`/cart`, `/orders`, `/profile`, `/addresses`) under a `<ProtectedRoute requiredRoles={['CLIENT', 'ADMIN']}>` layout route with `<Outlet />`
- [x] 3.4 Wrap STOCK routes (`/admin/productos`, `/admin/categorias`, `/admin/ingredientes`) under `<ProtectedRoute requiredRoles={['STOCK', 'ADMIN']}>`
- [x] 3.5 Wrap PEDIDOS route (`/admin/pedidos`) under `<ProtectedRoute requiredRoles={['PEDIDOS', 'ADMIN']}>`
- [x] 3.6 Wrap ADMIN-only routes (`/admin/usuarios`, `/admin/metricas`, `/admin/configuracion`) under `<ProtectedRoute requiredRoles={['ADMIN']}>`
- [x] 3.7 Add page stub imports for new admin sub-routes (use `Admin` page as placeholder until dedicated pages exist)

## 4. Write vitest tests for ProtectedRoute

- [x] 4.1 Create `frontend/src/shared/routing/__tests__/ProtectedRoute.test.tsx`
- [x] 4.2 Write test: `_hasHydrated = false` → renders loading indicator, NOT a redirect
- [x] 4.3 Write test: `isAuthenticated = false`, `_hasHydrated = true` → redirects to `/login`
- [x] 4.4 Write test: `isAuthenticated = true`, `requiredRoles = ['ADMIN']`, user has no matching role → redirects to `/403`
- [x] 4.5 Write test: `isAuthenticated = true`, `requiredRoles = ['CLIENT', 'ADMIN']`, user has role `ADMIN` → renders `<Outlet />` content
- [x] 4.6 Write test: `isAuthenticated = true`, no `requiredRoles` → renders `<Outlet />` content (auth-only route)
- [x] 4.7 Mock `useAuthStore` with `vi.mock('@/store/authStore')` for all tests

## 5. Verify and validate

- [x] 5.1 Run `cd frontend && npx tsc --noEmit` — zero TypeScript errors
- [x] 5.2 Run `cd frontend && npx vitest run` — all tests pass including new ProtectedRoute tests
