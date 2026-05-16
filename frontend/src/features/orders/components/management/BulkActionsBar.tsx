/**
 * BulkActionsBar — floating action bar shown when orders are selected.
 *
 * Reads selectedIds from ordersManagementStore.
 * If selectedIds.size === 0, renders nothing.
 *
 * Buttons:
 *   - "Cambiar estado masivo" — disabled (aria-disabled) when selected orders have
 *     mixed states; enabled only when all selected share the same estado_pedido_id.
 *   - "Cancelar seleccionados" — always enabled when selection is non-empty.
 *
 * Both destructive actions require BulkConfirmModal confirmation before executing.
 *
 * Accessibility: role="toolbar", aria-label, aria-disabled with message on mixed state.
 * All colors via semantic @theme tokens — zero hardcoded colors.
 */

import { useState, useMemo } from 'react'
import { X, Trash2, ArrowRightLeft } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'
import { BulkConfirmModal } from '@/features/orders/components/management/BulkConfirmModal'
import { StateTransitionModal } from '@/features/orders/components/management/StateTransitionModal'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'
import { useBulkOrderActions } from '@/features/orders/hooks/useBulkOrderActions'
import type { Order } from '@/features/orders/types'

export interface BulkActionsBarProps {
  /** Current page of orders — needed to derive mixed/shared status */
  orders: Order[]
}

export function BulkActionsBar({ orders }: BulkActionsBarProps) {
  const selectedIds    = useOrdersManagementStore((s) => s.selectedIds)
  const isBulkPending  = useOrdersManagementStore((s) => s.isBulkPending)
  const clearAll       = useOrdersManagementStore((s) => s.clearAll)

  const { bulkCancel } = useBulkOrderActions()

  const [cancelConfirmOpen,  setCancelConfirmOpen]  = useState(false)
  const [stateModalOpen,     setStateModalOpen]     = useState(false)

  // Derive shared status: all selected orders share the same estado_pedido_id
  const sharedStatusId = useMemo<number | null>(() => {
    if (selectedIds.size === 0) return null
    const selectedOrders = orders.filter((o) => selectedIds.has(o.id))
    if (selectedOrders.length === 0) return null
    const first = selectedOrders[0].estado_pedido_id
    const allSame = selectedOrders.every((o) => o.estado_pedido_id === first)
    return allSame ? first : null
  }, [selectedIds, orders])

  const selectedCount = selectedIds.size

  // Nothing selected — render nothing (no DOM node at all)
  if (selectedCount === 0) return null

  const selectedArray = Array.from(selectedIds)
  const mixedState = sharedStatusId === null

  const handleBulkCancel = async () => {
    setCancelConfirmOpen(false)
    await bulkCancel(selectedArray)
  }

  return (
    <>
      {/* Sticky bar at bottom of table area */}
      <div
        role="toolbar"
        aria-label="Acciones para pedidos seleccionados"
        className={[
          'flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card px-4 py-3',
          'shadow-md',
        ].join(' ')}
      >
        {/* Count + clear */}
        <div className="flex items-center gap-2 mr-auto min-w-0">
          <span className="text-sm font-medium text-foreground">
            {selectedCount} {selectedCount === 1 ? 'pedido seleccionado' : 'pedidos seleccionados'}
          </span>
          <button
            type="button"
            onClick={clearAll}
            aria-label="Limpiar selección"
            className={[
              'h-6 w-6 rounded inline-flex items-center justify-center',
              'text-muted-foreground hover:text-foreground hover:bg-accent',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            ].join(' ')}
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>

        {/* Bulk state change */}
        <div className="relative">
          <Button
            variant="outline"
            size="sm"
            onClick={() => !mixedState && setStateModalOpen(true)}
            disabled={mixedState || isBulkPending}
            aria-disabled={mixedState || isBulkPending}
            aria-describedby={mixedState ? 'bulk-state-disabled-hint' : undefined}
          >
            <ArrowRightLeft className="h-4 w-4" aria-hidden="true" />
            Cambiar estado
          </Button>
          {mixedState && (
            <span
              id="bulk-state-disabled-hint"
              className="sr-only"
            >
              No disponible: los pedidos seleccionados tienen estados diferentes
            </span>
          )}
        </div>

        {/* Bulk cancel */}
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setCancelConfirmOpen(true)}
          disabled={isBulkPending}
          loading={isBulkPending}
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
          Cancelar seleccionados
        </Button>
      </div>

      {/* Confirm cancel modal */}
      <BulkConfirmModal
        isOpen={cancelConfirmOpen}
        onClose={() => setCancelConfirmOpen(false)}
        onConfirm={handleBulkCancel}
        title="Cancelar pedidos"
        message={`¿Seguro que querés cancelar ${selectedCount} ${selectedCount === 1 ? 'pedido' : 'pedidos'}? Esta acción no se puede deshacer.`}
        confirmLabel={`Cancelar ${selectedCount} ${selectedCount === 1 ? 'pedido' : 'pedidos'}`}
        isPending={isBulkPending}
      />

      {/* Bulk state transition modal */}
      {!mixedState && sharedStatusId !== null && (
        <StateTransitionModal
          orderId={selectedArray[0] ?? 0}
          currentStatusId={sharedStatusId}
          isOpen={stateModalOpen}
          onClose={() => setStateModalOpen(false)}
          isBulkMode
          bulkOrderIds={selectedArray}
        />
      )}
    </>
  )
}
