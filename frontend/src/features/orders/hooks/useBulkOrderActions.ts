/**
 * useBulkOrderActions — wrapper around Promise.allSettled for bulk order operations.
 *
 * Returns helpers for:
 *   - bulkCancel(ids): cancels multiple orders via DELETE /api/v1/pedidos/{id}
 *   - bulkAdvanceState(ids, nuevoEstadoId): advances multiple orders via PATCH
 *
 * Both return { succeeded: number[], failed: number[] } so the caller can
 * display a partial-success summary toast.
 *
 * Uses the shared apiClient directly (not the mutation hooks) so we can
 * call allSettled without React mutation lifecycle coupling.
 *
 * After completion:
 *   - Invalidates ['orders'] cache
 *   - Adds a summary toast via useUIStore
 */

import { useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useUIStore } from '@/store/uiStore'
import { ORDERS_QUERY_KEY } from '@/features/orders/hooks/useOrders'
import { useOrdersManagementStore } from '@/features/orders/store/ordersManagementStore'

export interface BulkResult {
  succeeded: number[]
  failed: number[]
}

export function useBulkOrderActions() {
  const queryClient = useQueryClient()
  const addToast = useUIStore((state) => state.addToast)
  const setIsBulkPending = useOrdersManagementStore((s) => s.setIsBulkPending)
  const clearAll = useOrdersManagementStore((s) => s.clearAll)

  /**
   * Cancel multiple orders via DELETE /api/v1/pedidos/{id}.
   * Uses Promise.allSettled so partial failures are handled gracefully.
   */
  async function bulkCancel(ids: number[]): Promise<BulkResult> {
    setIsBulkPending(true)
    try {
      const results = await Promise.allSettled(
        ids.map((id) => apiClient.delete(`/api/v1/pedidos/${id}`)),
      )

      const succeeded: number[] = []
      const failed: number[] = []

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          succeeded.push(ids[index])
        } else {
          failed.push(ids[index])
        }
      })

      // Invalidate listing cache
      void queryClient.invalidateQueries({ queryKey: [ORDERS_QUERY_KEY] })

      // Toast with summary
      if (failed.length === 0) {
        addToast({
          message: `${succeeded.length} ${succeeded.length === 1 ? 'pedido cancelado' : 'pedidos cancelados'} correctamente`,
          type: 'success',
        })
      } else if (succeeded.length === 0) {
        addToast({
          message: `No se pudo cancelar ningún pedido (${failed.length} fallidos)`,
          type: 'error',
        })
      } else {
        addToast({
          message: `${succeeded.length} cancelados, ${failed.length} fallidos`,
          type: 'error',
        })
      }

      // Clear selection after bulk operation
      clearAll()

      return { succeeded, failed }
    } finally {
      setIsBulkPending(false)
    }
  }

  /**
   * Advance multiple orders to a new state via PATCH /api/v1/pedidos/{id}/estado.
   * Uses Promise.allSettled so partial failures are handled gracefully.
   */
  async function bulkAdvanceState(ids: number[], nuevoEstadoId: number): Promise<BulkResult> {
    setIsBulkPending(true)
    try {
      const results = await Promise.allSettled(
        ids.map((id) =>
          apiClient.patch(`/api/v1/pedidos/${id}/estado`, { nuevo_estado_id: nuevoEstadoId }),
        ),
      )

      const succeeded: number[] = []
      const failed: number[] = []

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          succeeded.push(ids[index])
        } else {
          failed.push(ids[index])
        }
      })

      // Invalidate listing cache
      void queryClient.invalidateQueries({ queryKey: [ORDERS_QUERY_KEY] })

      // Toast with summary
      if (failed.length === 0) {
        addToast({
          message: `Estado actualizado en ${succeeded.length} ${succeeded.length === 1 ? 'pedido' : 'pedidos'}`,
          type: 'success',
        })
      } else if (succeeded.length === 0) {
        addToast({
          message: `No se pudo actualizar ningún estado (${failed.length} fallidos)`,
          type: 'error',
        })
      } else {
        addToast({
          message: `${succeeded.length} actualizados, ${failed.length} fallidos`,
          type: 'error',
        })
      }

      // Clear selection after bulk operation
      clearAll()

      return { succeeded, failed }
    } finally {
      setIsBulkPending(false)
    }
  }

  return { bulkCancel, bulkAdvanceState }
}
