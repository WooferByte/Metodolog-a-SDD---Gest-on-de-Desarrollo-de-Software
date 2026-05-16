/**
 * OrderActions — renders available actions for an order based on role and FSM state.
 *
 * CLIENT mode (adminMode=false):
 *   - Shows "Cancelar pedido" button
 *   - Enabled only when estado_pedido_id === 1 (PENDIENTE)
 *   - Disabled with aria-disabled + title tooltip when not cancellable
 *   - Clicking enabled button opens CancelOrderModal (via useOrderDetailStore)
 *
 * Admin mode (adminMode=true):
 *   - Shows state advance selector based on VALID_TRANSITIONS FSM matrix
 *   - Terminal states (5, 6) show a "closed order" message with no buttons
 *   - Pending state (1) shows no manual advance (system/webhook only)
 *
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { ORDER_STATUS_MAP } from '@/features/orders/constants/orderStatus'
import {
  VALID_TRANSITIONS,
  isTerminalState,
} from '@/features/orders/constants/orderTransitions'
import { useOrderDetailStore } from '@/features/orders/store/orderDetailStore'
import { useAdvanceOrderState } from '@/features/orders/hooks/useAdvanceOrderState'
import type { OrderDetail } from '@/features/orders/types'

export interface OrderActionsProps {
  order: OrderDetail
  adminMode?: boolean
}

export function OrderActions({ order, adminMode = false }: OrderActionsProps) {
  const openCancelModal = useOrderDetailStore((state) => state.openCancelModal)
  const { mutate: advanceState, isPending: isAdvancing } = useAdvanceOrderState()
  const [selectedNextState, setSelectedNextState] = useState<number | null>(null)

  const currentStateId = order.estado_pedido_id

  // ── CLIENT mode ──────────────────────────────────────────────────────────
  if (!adminMode) {
    const canCancel = currentStateId === 1    // PENDIENTE only

    return (
      <div className="rounded-xl border border-border bg-card p-4 md:p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">
          Acciones
        </h2>
        <Button
          variant="destructive"
          size="md"
          onClick={canCancel ? openCancelModal : undefined}
          disabled={!canCancel}
          aria-disabled={!canCancel}
          title={
            !canCancel
              ? 'El pedido no puede cancelarse en este estado'
              : undefined
          }
          aria-label={
            canCancel
              ? `Cancelar pedido #${order.id}`
              : `No se puede cancelar el pedido #${order.id} en estado actual`
          }
        >
          Cancelar pedido
        </Button>
      </div>
    )
  }

  // ── Admin mode ────────────────────────────────────────────────────────────

  // Terminal states — no actions available
  if (isTerminalState(currentStateId)) {
    const statusLabel = ORDER_STATUS_MAP[currentStateId]?.label ?? 'Cerrado'
    return (
      <div className="rounded-xl border border-border bg-card p-4 md:p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">
          Acciones
        </h2>
        <p className="text-sm text-muted-foreground">
          Este pedido está cerrado ({statusLabel}). No hay acciones disponibles.
        </p>
      </div>
    )
  }

  const availableTransitions = VALID_TRANSITIONS[currentStateId] ?? []

  // State 1 (PENDIENTE) — no manual advance (system/webhook only)
  if (availableTransitions.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 md:p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">
          Acciones
        </h2>
        <p className="text-sm text-muted-foreground">
          Este pedido está pendiente de confirmación por el sistema.
          No hay acciones manuales disponibles.
        </p>
      </div>
    )
  }

  // Has valid manual transitions
  const handleAdvance = () => {
    if (selectedNextState === null) return
    advanceState({ orderId: order.id, nuevoEstadoId: selectedNextState })
    setSelectedNextState(null)
  }

  return (
    <div className="rounded-xl border border-border bg-card p-4 md:p-6">
      <h2 className="mb-3 text-base font-semibold text-foreground">
        Acciones de administrador
      </h2>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        {/* State selector */}
        <div className="flex flex-col gap-1.5 flex-1">
          <label
            htmlFor="next-state-select"
            className="text-sm font-medium text-foreground"
          >
            Avanzar al estado:
          </label>
          <select
            id="next-state-select"
            value={selectedNextState ?? ''}
            onChange={(e) =>
              setSelectedNextState(e.target.value ? Number(e.target.value) : null)
            }
            className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Seleccionar nuevo estado del pedido"
          >
            <option value="">-- Seleccionar estado --</option>
            {availableTransitions.map((stateId) => {
              const meta = ORDER_STATUS_MAP[stateId]
              return (
                <option key={stateId} value={stateId}>
                  {meta?.label ?? `Estado #${stateId}`}
                </option>
              )
            })}
          </select>
        </div>

        {/* Confirm button */}
        <Button
          variant="primary"
          size="md"
          onClick={handleAdvance}
          disabled={selectedNextState === null || isAdvancing}
          loading={isAdvancing}
          aria-label="Confirmar cambio de estado del pedido"
        >
          Confirmar cambio
        </Button>
      </div>
    </div>
  )
}
