/**
 * OrdersTable — semantic HTML table for the admin orders panel.
 *
 * Design decision D7 (design.md): Uses <table> native with role="table",
 * <th scope="col">, <thead>, <tbody> for maximum screen reader compatibility
 * with relational tabular data.
 *
 * When isLoading=true, renders OrdersSkeleton rows inside <tbody>.
 * When items.length===0 (and not loading), renders a single empty-state row.
 *
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { OrdersSkeleton } from '@/features/orders/components/OrdersSkeleton'
import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import { Button } from '@/shared/components/ui/Button'
import type { Order } from '@/features/orders/types'

export interface OrdersTableProps {
  orders: Order[]
  isLoading: boolean
  onViewDetail: (id: number) => void
}

/** Format a number as ARS currency */
function formatARS(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount)
}

/** Format ISO datetime to locale date string */
function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return isoString
  }
}

export function OrdersTable({ orders, isLoading, onViewDetail }: OrdersTableProps) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-border">
      <table
        role="table"
        className="w-full border-collapse text-sm"
        aria-label="Tabla de pedidos"
      >
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              # Pedido
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Fecha
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Total
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Estado
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Acciones
            </th>
          </tr>
        </thead>

        <tbody>
          {isLoading ? (
            <OrdersSkeleton mode="admin" count={5} />
          ) : orders.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="px-4 py-12 text-center text-sm text-muted-foreground"
              >
                No hay pedidos registrados
              </td>
            </tr>
          ) : (
            orders.map((order) => (
              <tr
                key={order.id}
                className="border-b border-border last:border-0 hover:bg-muted/20 transition-colors"
              >
                {/* # Pedido */}
                <td className="px-4 py-3 font-mono text-sm text-foreground">
                  #{order.id}
                </td>

                {/* Fecha */}
                <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap">
                  <time dateTime={order.creado_en}>
                    {formatDate(order.creado_en)}
                  </time>
                </td>

                {/* Total */}
                <td className="px-4 py-3 text-right text-sm font-semibold text-foreground whitespace-nowrap">
                  {formatARS(order.total)}
                </td>

                {/* Estado */}
                <td className="px-4 py-3">
                  <OrderStatusBadge statusId={order.estado_pedido_id} />
                </td>

                {/* Acciones */}
                <td className="px-4 py-3 text-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onViewDetail(order.id)}
                    aria-label={`Ver detalle del pedido #${order.id}`}
                  >
                    Ver detalle
                  </Button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
