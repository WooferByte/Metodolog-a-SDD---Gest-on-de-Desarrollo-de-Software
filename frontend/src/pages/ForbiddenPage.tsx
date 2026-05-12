import { useNavigate } from 'react-router-dom'

/**
 * ForbiddenPage — 403 Access Denied screen.
 *
 * Rendered when a user navigates to /403 or is redirected there by ProtectedRoute
 * because they lack the required role(s).
 *
 * Accessibility: WCAG 2.1 AA — semantic heading, visible focus ring, sufficient contrast.
 * Styling: Tailwind v4 utility classes only (no inline style props).
 */
export default function ForbiddenPage() {
  const navigate = useNavigate()

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 text-center">
      <div className="max-w-md space-y-6">
        {/* Error code */}
        <p className="text-6xl font-bold text-red-500" aria-hidden="true">
          403
        </p>

        {/* Main heading */}
        <h1 className="text-2xl font-semibold text-gray-900">
          Acceso denegado
        </h1>

        {/* Description */}
        <p className="text-base text-gray-600">
          No tenés permisos para ver esta página. Si creés que esto es un
          error, contactá al administrador.
        </p>

        {/* Navigation button */}
        <button
          type="button"
          onClick={() => navigate('/')}
          className="inline-flex items-center rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-50"
        >
          Volver al inicio
        </button>
      </div>
    </main>
  )
}
