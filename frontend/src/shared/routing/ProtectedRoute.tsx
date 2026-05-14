import { useLocation, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

/**
 * ProtectedRoute — layout route component for react-router-dom v6 nested routes.
 *
 * Guards:
 * 1. `_hasHydrated = false` → show loading spinner (avoid redirect flash on page reload)
 * 2. `!isAuthenticated`     → redirect to /login with `state.from` for post-login redirect
 * 3. `requiredRoles` defined and user lacks all of them → redirect to /403
 * 4. All checks pass        → render <Outlet /> (child routes)
 *
 * Usage:
 * ```tsx
 * <Route element={<ProtectedRoute requiredRoles={['ADMIN']} />}>
 *   <Route path="/admin/usuarios" element={<AdminUsuarios />} />
 * </Route>
 * ```
 */
export interface ProtectedRouteProps {
  requiredRoles?: string[]
}

export function ProtectedRoute({ requiredRoles }: ProtectedRouteProps) {
  const location = useLocation()
  const _hasHydrated = useAuthStore((state) => state._hasHydrated)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasRole = useAuthStore((state) => state.hasRole)

  // Guard 1: Wait for Zustand to rehydrate from localStorage before redirecting.
  // Without this, every page reload would flash-redirect to /login for one frame.
  if (!_hasHydrated) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        role="status"
        aria-label="Cargando..."
      >
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-border border-t-foreground" />
      </div>
    )
  }

  // Guard 2: Not authenticated → send to login.
  // Only preserve `from` for non-role-restricted routes. If the route requires
  // specific roles, don't save `from` — a different user logging in next would
  // get redirected there and hit /403 (e.g. admin logs out on /admin/dashboard,
  // client logs in and gets sent to /admin/dashboard → access denied).
  if (!isAuthenticated) {
    const from = requiredRoles?.length ? undefined : { from: location }
    return <Navigate to="/login" state={from} replace />
  }

  // Guard 3: Role check — user must have at least one of the required roles
  if (requiredRoles && requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some((role) => hasRole(role))
    if (!hasRequiredRole) {
      return <Navigate to="/403" replace />
    }
  }

  // All checks pass — render child routes
  return <Outlet />
}
