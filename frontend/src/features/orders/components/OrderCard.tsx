/**
 * OrderCard — shared component for displaying a single order.
 *
 * Design decision D2 (design.md): One component with mode prop instead of
 * two separate components, to avoid duplicating badge + date/total formatting.
 *
 * mode="client" → full timeline card with status badge, date, total, CTA button
 * mode="admin"  → compact row-like layout for use inside admin contexts
 *
 * All colors via semantic @theme tokens — zero hardcoded colors.
 * Mobile-first: readable at 375px viewport without horizontal overflow.
 */

import { Link } from 'react-router-dom'
import { cn } from '@/shared/lib/utils'
import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import type { Order } from '@/features/orders/types'

export interface OrderCardProps {
  order: Order
  mode: 'client' | 'admin'
  onViewDetail?: (id: number) => void
  className?: string
}

/** Format a date string to a human-readable Spanish locale date */
function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return isoString
  }
}

/** Format a number as ARS currency */
function formatARS(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount)
}

export function OrderCard({ order, mode, onViewDetail, className }: OrderCardProps) {
  if (mode === 'client') {
    return (
      <article
        className={cn(
          'rounded-xl border border-border bg-card p-4',
          'flex flex-col gap-3',
          // Mobile-first: full-width, no horizontal overflow
          'w-full min-w-0',
          className,
        )}
        aria-label={`Pedido #${order.id}`}
      >
        {/* Header: badge + date */}
        <header className="flex items-start justify-between gap-2 flex-wrap">
          <OrderStatusBadge statusId={order.estado_pedido_id} />
          <time
            dateTime={order.creado_en}
            className="text-xs text-muted-foreground shrink-0"
          >
            {formatDate(order.creado_en)}
          </time>
        </header>

        {/* Body: order ID + observation if present */}
        <div className="flex flex-col gap-1 min-w-0">
          <p className="text-sm font-medium text-foreground">
            Pedido{' '}
            <span className="font-mono text-muted-foreground">
              #{order.id}
            </span>
          </p>
          {order.observacion && (
            <p className="text-xs text-muted-foreground truncate">
              {order.observacion}
            </p>
          )}
        </div>

        {/* Footer: total + CTA */}
        <footer className="flex items-center justify-between gap-2 mt-auto flex-wrap">
          <p className="text-base font-semibold text-foreground">
            {formatARS(order.total)}
          </p>
          <Link
            to={`/pedidos/${order.id}`}
            aria-label={`Ver detalle del pedido #${order.id}`}
            onClick={() => onViewDetail?.(order.id)}
            className={cn(
              'inline-flex items-center justify-center gap-2 font-medium',
              'transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ring',
              'border border-border bg-transparent text-foreground',
              'hover:bg-accent hover:text-accent-foreground',
              'h-8 px-3 text-sm rounded-md',
            )}
          >
            Ver detalle
          </Link>
        </footer>
      </article>
    )
  }

  // mode === 'admin' — compact layout for table context
  return (
    <div
      className={cn(
        'flex items-center gap-3 min-w-0',
        className,
      )}
      aria-label={`Pedido #${order.id}`}
    >
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-sm font-medium text-foreground font-mono">
          #{order.id}
        </span>
        <time
          dateTime={order.creado_en}
          className="text-xs text-muted-foreground"
        >
          {formatDate(order.creado_en)}
        </time>
      </div>

      <OrderStatusBadge statusId={order.estado_pedido_id} className="shrink-0" />

      <span className="ml-auto text-sm font-semibold text-foreground shrink-0">
        {formatARS(order.total)}
      </span>

      <Link
        to={`/admin/pedidos/${order.id}`}
        aria-label={`Ver detalle del pedido #${order.id}`}
        onClick={() => onViewDetail?.(order.id)}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium',
          'transition-colors duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ring',
          'border border-border bg-transparent text-foreground',
          'hover:bg-accent hover:text-accent-foreground',
          'h-8 px-3 text-sm rounded-md shrink-0',
        )}
      >
        Ver
      </Link>
    </div>
  )
}
