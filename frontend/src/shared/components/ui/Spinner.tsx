/**
 * Spinner — full-page loading indicator using semantic tokens.
 *
 * Used as the Suspense fallback in Router.tsx during lazy-loaded page transitions.
 * Markup matches the ProtectedRoute hydration spinner to avoid visual inconsistency.
 */
export function Spinner() {
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
