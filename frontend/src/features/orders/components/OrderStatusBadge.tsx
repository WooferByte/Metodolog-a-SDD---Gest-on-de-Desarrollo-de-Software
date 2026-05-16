/**
 * OrderStatusBadge — renders a semantic badge for a pedido's estado_pedido_id.
 *
 * - Looks up label and Tailwind v4 semantic token classes from ORDER_STATUS_MAP.
 * - Falls back to "Desconocido" + muted styling for unknown IDs.
 * - Adds aria-label for screen reader accessibility (WCAG AA).
 * - Zero hardcoded colors — all via @theme tokens.
 */

import { cn } from '@/shared/lib/utils'
import {
  ORDER_STATUS_MAP,
  UNKNOWN_STATUS,
} from '@/features/orders/constants/orderStatus'

export interface OrderStatusBadgeProps {
  statusId: number
  className?: string
}

export function OrderStatusBadge({ statusId, className }: OrderStatusBadgeProps) {
  const meta = ORDER_STATUS_MAP[statusId] ?? UNKNOWN_STATUS

  return (
    <span
      aria-label={`Estado del pedido: ${meta.label}`}
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5',
        'text-xs font-semibold',
        meta.bgClass,
        meta.textClass,
        className,
      )}
    >
      {meta.label}
    </span>
  )
}
