import { ComponentType } from 'react'
import { Navigate } from 'react-router-dom'

/**
 * withAuth Higher-Order Component
 * Protects routes by requiring authentication and optional role-based access
 * 
 * @param Component - The component to protect
 * @param requiredRoles - Optional array of required roles (will be implemented in CHANGE 6)
 * @returns Protected component that redirects to login if not authenticated
 */
export function withAuth<P extends object>(
  Component: ComponentType<P>,
  requiredRoles?: string[]
) {
  return function ProtectedComponent(props: P) {
    // TODO: Integrate with authStore in CHANGE 6
    // For now, always render (placeholder)
    const isAuthenticated = true // Will be replaced with: authStore.isAuthenticated
    const userRoles: string[] = [] // Will be replaced with: authStore.user?.roles || []

    // Check authentication
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />
    }

    // Check roles if required
    if (requiredRoles && requiredRoles.length > 0) {
      const hasRequiredRole = requiredRoles.some((role) =>
        userRoles.includes(role)
      )

      if (!hasRequiredRole) {
        return (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              backgroundColor: '#f3f4f6',
              minHeight: '100vh',
            }}
          >
            <h1>403 - Acceso Denegado</h1>
            <p>No tienes permisos para acceder a esta página.</p>
            <a href="/">Volver al inicio</a>
          </div>
        )
      }
    }

    return <Component {...props} />
  }
}
