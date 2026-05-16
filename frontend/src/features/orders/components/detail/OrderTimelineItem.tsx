/**
 * OrderTimelineItem — single item in the order FSM history timeline.
 *
 * Shows: status badge, timestamp formatted in Spanish, responsible user email
 * (or "Sistema" fallback when usuario_email is null).
 *
 * Animation: slide-in CSS animation with inline animation-delay per index
 * (set by parent OrderTimeline). Uses --animate-slide-in token from @theme.
 *
 * Decorative elements (line, dot) have aria-hidden="true".
 * Text content is fully accessible to screen readers.
 */

import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import type { OrderHistorialItem } from '@/features/orders/types'

export interface OrderTimelineItemProps {
  item: OrderHistorialItem
  isLast: boolean
  /** Index used to calculate animation-delay for staggered entry */
  index: number
}

/** Format ISO datetime to readable Spanish locale date+time */
function formatDateTime(isoString: string): string {
  try {
    return new Intl.DateTimeFormat('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(isoString))
  } catch {
    return isoString
  }
}

export function OrderTimelineItem({ item, isLast, index }: OrderTimelineItemProps) {
  const userLabel = item.usuario_email ?? `Usuario #${item.usuario_responsable_id ?? '?'}`

  return (
    <li
      className="relative flex gap-4"
      style={{
        animation: 'slide-in 0.3s ease-out both',
        animationDelay: `${index * 0.1}s`,
      }}
    >
      {/* Vertical connector line */}
      {!isLast && (
        <div
          aria-hidden="true"
          className="absolute left-3.5 top-7 h-full w-px bg-border"
        />
      )}

      {/* Circular dot */}
      <div
        aria-hidden="true"
        className="relative z-10 mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-border bg-card"
      >
        <div className="h-2 w-2 rounded-full bg-muted-foreground" />
      </div>

      {/* Content */}
      <div className="flex min-w-0 flex-1 flex-col gap-1 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <OrderStatusBadge statusId={item.estado_nuevo_id} />
        </div>
        <div className="flex flex-col gap-0.5 text-xs text-muted-foreground">
          <time dateTime={item.creado_en}>
            {formatDateTime(item.creado_en)}
          </time>
          <span>
            {item.usuario_email === null ? 'Sistema' : userLabel}
          </span>
        </div>
      </div>
    </li>
  )
}
