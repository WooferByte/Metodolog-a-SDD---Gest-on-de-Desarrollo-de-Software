/**
 * OrderItemSnapshot — renders a single order line item with snapshot data.
 *
 * CRITICAL: All data shown here is the snapshot captured at order creation time.
 * nombre_snapshot and precio_snapshot are FROZEN values — never live product data.
 * This component NEVER makes additional requests to /api/v1/productos.
 *
 * Shows: product name (snapshot), quantity, unit price (snapshot), subtotal.
 * If ingredientes_excluidos has items: shows "Ingrediente #ID" fallback labels.
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import type { OrderDetailItem } from '@/features/orders/types'

export interface OrderItemSnapshotProps {
  item: OrderDetailItem
}

/** Format a number as ARS currency */
function formatARS(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount)
}

export function OrderItemSnapshot({ item }: OrderItemSnapshotProps) {
  const subtotal = item.cantidad * item.precio_snapshot
  const hasExcluidos = item.ingredientes_excluidos && item.ingredientes_excluidos.length > 0

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4">
      {/* Product name + quantity */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-foreground">
            {item.nombre_snapshot}
          </p>
          <p className="text-xs text-muted-foreground">
            {item.cantidad} × {formatARS(item.precio_snapshot)}
          </p>
        </div>
        <p className="shrink-0 text-sm font-semibold text-foreground">
          {formatARS(subtotal)}
        </p>
      </div>

      {/* Excluded ingredients — only rendered if non-empty */}
      {hasExcluidos && (
        <div className="border-t border-border pt-2">
          <p className="mb-1 text-xs font-medium text-muted-foreground">
            Personalizaciones:
          </p>
          <ul
            role="list"
            className="flex flex-wrap gap-1"
          >
            {item.ingredientes_excluidos!.map((ingredientId) => (
              <li
                key={ingredientId}
                className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
              >
                Ingrediente #{ingredientId}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
