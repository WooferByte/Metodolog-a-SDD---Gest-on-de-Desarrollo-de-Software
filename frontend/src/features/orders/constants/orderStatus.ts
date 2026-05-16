/**
 * ORDER_STATUS_MAP — maps backend estado_pedido_id (number) to display metadata.
 *
 * Design decision D3 (design.md): Use Record<number, OrderStatusMeta> instead
 * of a TypeScript enum because IDs arrive as numbers from backend JSON and
 * enums require extra casting.
 *
 * Color tokens MUST be @theme semantic tokens from index.css — no raw colors.
 *
 * Mapping:
 *   1 = PENDIENTE     → warning   (yellow)
 *   2 = CONFIRMADO    → info      (blue)
 *   3 = EN_PREPARACIÓN → accent-orange (orange)
 *   4 = EN_CAMINO     → accent-purple (purple)
 *   5 = ENTREGADO     → success   (green)
 *   6 = CANCELADO     → muted     (grey)
 */

import type { OrderStatusMeta } from '@/features/orders/types'

export const ORDER_STATUS_MAP: Record<number, OrderStatusMeta> = {
  1: {
    id: 1,
    label: 'Pendiente',
    bgClass: 'bg-warning/10',
    textClass: 'text-warning',
  },
  2: {
    id: 2,
    label: 'Confirmado',
    bgClass: 'bg-info/10',
    textClass: 'text-info',
  },
  3: {
    id: 3,
    label: 'En preparación',
    bgClass: 'bg-accent-orange/10',
    textClass: 'text-accent-orange',
  },
  4: {
    id: 4,
    label: 'En camino',
    bgClass: 'bg-accent-purple/10',
    textClass: 'text-accent-purple',
  },
  5: {
    id: 5,
    label: 'Entregado',
    bgClass: 'bg-success/10',
    textClass: 'text-success',
  },
  6: {
    id: 6,
    label: 'Cancelado',
    bgClass: 'bg-muted',
    textClass: 'text-muted-foreground',
  },
}

/** Fallback metadata for unknown status IDs */
export const UNKNOWN_STATUS: OrderStatusMeta = {
  id: -1,
  label: 'Desconocido',
  bgClass: 'bg-muted',
  textClass: 'text-muted-foreground',
}
