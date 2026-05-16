/**
 * OrdersManagementRow — single row inside OrdersManagementTable.
 *
 * Columns: checkbox | # Pedido | Fecha | Total | Estado | Usuario | Acciones
 *
 * Checkbox:
 *   - Reads isSelected from ordersManagementStore
 *   - Calls toggleId on change
 *   - aria-label="Seleccionar pedido #X"
 *   - aria-checked reflects current selection state
 *
 * Acciones column:
 *   - "Ver detalle" button → onViewDetail(id)
 *   - "Cambiar estado" button → onStateChange(id)
 *     disabled if isTerminalState(estado_pedido_id), with tooltip text
 *
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useRef } from 'react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/components/ui/Button'
import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'
import { isTerminalState } from '@/features/orders/constants/orderTransitions'
import type { Order } from '@/features/orders/types'

export interface OrdersManagementRowProps {
  order: Order
  onViewDetail: (id: number) => void
  onStateChange: (id: number) => void
}

function formatARS(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount)
}

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

export function OrdersManagementRow({ order, onViewDetail, onStateChange }: OrdersManagementRowProps) {
  const checkboxRef = useRef<HTMLInputElement>(null)
  const isSelected  = useOrdersManagementStore((s) => s.selectedIds.has(order.id))
  const toggleId    = useOrdersManagementStore((s) => s.toggleId)
  const terminal    = isTerminalState(order.estado_pedido_id)

  return (
    <tr
      role="row"
      aria-selected={isSelected}
      className={cn(
        'border-b border-border last:border-0 transition-colors',
        isSelected ? 'bg-primary/5' : 'hover:bg-muted/20',
      )}
    >
      {/* Checkbox */}
      <td className="px-4 py-3 w-10">
        <input
          ref={checkboxRef}
          type="checkbox"
          checked={isSelected}
          onChange={() => toggleId(order.id)}
          aria-label={`Seleccionar pedido #${order.id}`}
          aria-checked={isSelected}
          className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
        />
      </td>

      {/* # Pedido */}
      <td className="px-4 py-3 font-mono text-sm text-foreground">
        #{order.id}
      </td>

      {/* Fecha */}
      <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap">
        <time dateTime={order.creado_en}>{formatDate(order.creado_en)}</time>
      </td>

      {/* Total */}
      <td className="px-4 py-3 text-right text-sm font-semibold text-foreground whitespace-nowrap">
        {formatARS(order.total)}
      </td>

      {/* Estado */}
      <td className="px-4 py-3">
        <OrderStatusBadge statusId={order.estado_pedido_id} />
      </td>

      {/* Usuario */}
      <td className="px-4 py-3 text-sm text-muted-foreground truncate max-w-[180px]">
        {'usuario_email' in order && (order as Order & { usuario_email?: string | null }).usuario_email
          ? (order as Order & { usuario_email?: string | null }).usuario_email
          : `#${order.usuario_id}`}
      </td>

      {/* Acciones */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 justify-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetail(order.id)}
            aria-label={`Ver detalle del pedido #${order.id}`}
          >
            Ver
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => !terminal && onStateChange(order.id)}
            disabled={terminal}
            aria-label={
              terminal
                ? `Pedido #${order.id} en estado terminal — sin transiciones`
                : `Cambiar estado del pedido #${order.id}`
            }
            title={terminal ? 'Estado terminal — sin transiciones posibles' : undefined}
          >
            Estado
          </Button>
        </div>
      </td>
    </tr>
  )
}
