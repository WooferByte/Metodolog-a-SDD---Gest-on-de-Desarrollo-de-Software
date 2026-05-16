/**
 * OrderTimeline — renders the FSM history of an order as a vertical timeline.
 *
 * Items are sorted chronologically (oldest first).
 * Each item has a staggered slide-in animation via inline animation-delay.
 *
 * Decorative elements (connecting lines, dots) have aria-hidden="true".
 * The list has role="list" for screen reader compatibility.
 * All text content (states, timestamps, users) is accessible.
 *
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useMemo } from 'react'
import { OrderTimelineItem } from '@/features/orders/components/detail/OrderTimelineItem'
import type { OrderHistorialItem } from '@/features/orders/types'

export interface OrderTimelineProps {
  historial: OrderHistorialItem[]
}

export function OrderTimeline({ historial }: OrderTimelineProps) {
  // Sort chronologically: oldest first (ascending by creado_en)
  const sorted = useMemo(
    () =>
      [...historial].sort(
        (a, b) => new Date(a.creado_en).getTime() - new Date(b.creado_en).getTime(),
      ),
    [historial],
  )

  if (sorted.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="text-sm text-muted-foreground">
          Sin historial de estados.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-border bg-card p-4 md:p-6">
      <h2 className="mb-4 text-base font-semibold text-foreground">
        Historial del pedido
      </h2>
      <ol role="list" className="space-y-0">
        {sorted.map((item, index) => (
          <OrderTimelineItem
            key={item.id}
            item={item}
            isLast={index === sorted.length - 1}
            index={index}
          />
        ))}
      </ol>
    </div>
  )
}
