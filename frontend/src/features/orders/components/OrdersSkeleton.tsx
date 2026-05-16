/**
 * OrdersSkeleton — loading placeholder matching the shape of the real content.
 *
 * Design decision D5 (design.md): Specific skeletons (not generic spinners)
 * to avoid CLS and provide a better loading UX.
 *
 * mode="client" → N card skeletons (timeline layout)
 * mode="admin"  → N table-row skeletons (inside <tbody>)
 *
 * Uses semantic tokens only — no hardcoded colors.
 */

import { cn } from '@/shared/lib/utils'

export interface OrdersSkeletonProps {
  mode: 'client' | 'admin'
  count?: number
}

/** Single skeleton card for client timeline view */
function ClientCardSkeleton() {
  return (
    <div
      role="status"
      aria-label="Cargando pedido..."
      className="rounded-xl border border-border bg-card p-4 animate-pulse"
    >
      {/* Header: badge + date */}
      <div className="flex items-center justify-between mb-3">
        <div className="h-5 w-24 rounded-full bg-muted" />
        <div className="h-4 w-28 rounded-md bg-muted" />
      </div>
      {/* Body lines */}
      <div className="space-y-2 mb-4">
        <div className="h-4 w-full rounded-md bg-muted" />
        <div className="h-4 w-3/4 rounded-md bg-muted" />
      </div>
      {/* Footer: total + CTA */}
      <div className="flex items-center justify-between">
        <div className="h-5 w-20 rounded-md bg-muted" />
        <div className="h-8 w-24 rounded-lg bg-muted" />
      </div>
    </div>
  )
}

/** Single skeleton row for admin table view */
function AdminRowSkeleton() {
  return (
    <tr aria-label="Cargando fila..." className="animate-pulse">
      {/* Email */}
      <td className="px-4 py-3">
        <div className="h-4 w-40 rounded-md bg-muted" />
      </td>
      {/* Fecha */}
      <td className="px-4 py-3">
        <div className="h-4 w-28 rounded-md bg-muted" />
      </td>
      {/* Total */}
      <td className="px-4 py-3">
        <div className="h-4 w-20 rounded-md bg-muted" />
      </td>
      {/* Estado */}
      <td className="px-4 py-3">
        <div className="h-5 w-24 rounded-full bg-muted" />
      </td>
      {/* Acciones */}
      <td className="px-4 py-3">
        <div className="h-8 w-24 rounded-lg bg-muted" />
      </td>
    </tr>
  )
}

export function OrdersSkeleton({ mode, count = 5 }: OrdersSkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i)

  if (mode === 'client') {
    return (
      <div
        className={cn(
          'grid gap-4',
          'grid-cols-1 sm:grid-cols-2',
        )}
        aria-live="polite"
        aria-busy="true"
      >
        {items.map((i) => (
          <ClientCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  // mode === 'admin' — returns <tbody> rows (table wrapper provided by OrdersTable)
  return (
    <>
      {items.map((i) => (
        <AdminRowSkeleton key={i} />
      ))}
    </>
  )
}
