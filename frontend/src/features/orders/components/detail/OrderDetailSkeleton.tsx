/**
 * OrderDetailSkeleton — loading placeholder for the order detail page.
 *
 * Matches the shape of the real detail layout: header, 3 item rows, 3 timeline items.
 * Uses animate-pulse with bg-muted for skeleton areas.
 *
 * Accessibility:
 *   - aria-hidden="true" on the entire skeleton container
 *   - sr-only text "Cargando detalle del pedido" for screen readers
 */

export function OrderDetailSkeleton() {
  return (
    <>
      {/* Screen reader announcement */}
      <p className="sr-only" role="status" aria-live="polite">
        Cargando detalle del pedido...
      </p>

      {/* Skeleton container — hidden from screen readers */}
      <div className="flex flex-col gap-4" aria-hidden="true">
        {/* Header skeleton */}
        <div className="rounded-xl border border-border bg-card p-4 md:p-6 animate-pulse">
          <div className="flex flex-col gap-3 md:flex-row md:justify-between">
            <div className="flex flex-col gap-2">
              <div className="h-7 w-48 rounded-lg bg-muted" />
              <div className="h-4 w-36 rounded-md bg-muted" />
            </div>
            <div className="flex gap-3 md:flex-col md:items-end md:gap-2">
              <div className="h-6 w-24 rounded-full bg-muted" />
              <div className="h-6 w-28 rounded-md bg-muted" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 border-t border-border pt-4">
            <div className="h-4 w-4 rounded-full bg-muted" />
            <div className="h-4 w-64 rounded-md bg-muted" />
          </div>
        </div>

        {/* Items skeleton */}
        <div className="rounded-xl border border-border bg-card p-4 md:p-6 animate-pulse">
          <div className="mb-4 h-5 w-32 rounded-md bg-muted" />
          <div className="flex flex-col gap-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-border p-4">
                <div className="flex flex-col gap-1.5 flex-1">
                  <div className="h-4 w-40 rounded-md bg-muted" />
                  <div className="h-3 w-28 rounded-md bg-muted" />
                </div>
                <div className="h-5 w-20 rounded-md bg-muted" />
              </div>
            ))}
          </div>
        </div>

        {/* Timeline skeleton */}
        <div className="rounded-xl border border-border bg-card p-4 md:p-6 animate-pulse">
          <div className="mb-4 h-5 w-40 rounded-md bg-muted" />
          <div className="flex flex-col gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="h-7 w-7 rounded-full bg-muted shrink-0" />
                <div className="flex flex-col gap-1.5 flex-1">
                  <div className="h-5 w-24 rounded-full bg-muted" />
                  <div className="h-3 w-36 rounded-md bg-muted" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions skeleton */}
        <div className="rounded-xl border border-border bg-card p-4 animate-pulse">
          <div className="h-9 w-36 rounded-lg bg-muted" />
        </div>
      </div>
    </>
  )
}
