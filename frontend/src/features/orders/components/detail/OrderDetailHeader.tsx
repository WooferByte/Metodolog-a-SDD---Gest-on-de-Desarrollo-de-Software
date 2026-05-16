/**
 * OrderDetailHeader — displays the header section of an order detail page.
 *
 * Shows: order number, formatted date, total in ARS, status badge, delivery address.
 * All data comes from the OrderDetail snapshot — no additional API calls.
 *
 * Responsive mobile-first: stack vertical on mobile, horizontal on md+.
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import type { OrderDetail } from '@/features/orders/types'

export interface OrderDetailHeaderProps {
  order: OrderDetail
}

/** Format an ISO datetime to a human-readable Spanish locale date+time */
function formatDateTime(isoString: string): string {
  try {
    return new Intl.DateTimeFormat('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(isoString))
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

export function OrderDetailHeader({ order }: OrderDetailHeaderProps) {
  const snap = order.direccion_snapshot
  const address = snap
    ? [snap.alias, snap.linea1, snap.ciudad, snap.codigo_postal]
        .filter(Boolean)
        .join(', ')
    : 'Dirección no disponible'

  return (
    <div className="rounded-xl border border-border bg-card p-4 md:p-6">
      {/* Top row: order number + badge */}
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-bold text-foreground md:text-2xl">
            Pedido{' '}
            <span className="font-mono text-muted-foreground">
              #{order.id}
            </span>
          </h1>
          <time
            dateTime={order.creado_en}
            className="text-sm text-muted-foreground"
          >
            {formatDateTime(order.creado_en)}
          </time>
        </div>

        <div className="flex flex-row items-center gap-3 md:flex-col md:items-end md:gap-2">
          <OrderStatusBadge statusId={order.estado_pedido_id} />
          <p className="text-lg font-semibold text-foreground md:text-xl">
            {formatARS(order.total)}
          </p>
        </div>
      </div>

      {/* Delivery address */}
      <div className="mt-4 flex items-start gap-2 border-t border-border pt-4">
        {/* Location pin icon */}
        <svg
          className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <p className="text-sm text-muted-foreground">
          <span className="sr-only">Dirección de entrega: </span>
          {address}
        </p>
      </div>
    </div>
  )
}
