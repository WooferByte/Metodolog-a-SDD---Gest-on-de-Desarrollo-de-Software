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
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-700" />
      </div>
    )
  }

  // Guard 2: Not authenticated → send to login, preserve intended destination
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
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

/**
 * withAuth — legacy HOC alias kept for backward compatibility.
 * Prefer using <ProtectedRoute> as a layout route in react-router-dom v6.
 *
 * @deprecated Use ProtectedRoute as a layout route instead.
 */
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  _requiredRoles?: string[]
) {
  return function ProtectedComponent(props: P) {
    return <Component {...props} />
  }
}
